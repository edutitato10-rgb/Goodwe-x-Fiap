"""Módulo de inteligência artificial (Sprint 1, seção 3.4).

1. Detecção de anomalias: Isolation Forest (não supervisionado) sobre as sessões fechadas.
2. Previsão de demanda: Regressão Linear (baseline) e XGBoost sobre a carga horária.
   A previsão usa apenas sessões NÃO sinalizadas, ou seja, a saída do passo 1 alimenta o passo 2.
"""
import json
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

FERIADOS = {date(2026, 9, 7), date(2026, 10, 12), date(2026, 11, 2), date(2026, 11, 15)}
FEATURES_ANOMALIA = ["duracao_h", "kwh", "pot_media_kw", "pot_max_kw", "cv_curva", "razao_energia_curva",
                     "hora_sin", "hora_cos", "dia_semana", "z_kwh_veiculo", "desvio_hora_veiculo"]
ROTULOS_LEGIVEIS = {
    "duracao_h": "duração incomum", "kwh": "energia total incomum",
    "pot_media_kw": "potência média incomum", "pot_max_kw": "potência máxima incomum",
    "cv_curva": "curva de potência instável", "razao_energia_curva": "energia incompatível com a curva de potência",
    "hora_sin": "horário atípico", "hora_cos": "horário atípico", "dia_semana": "dia da semana atípico",
    "z_kwh_veiculo": "consumo fora do padrão do veículo", "desvio_hora_veiculo": "horário fora do padrão do veículo",
}


# ---------------------------------------------------------------- anomalias
def _montar_features(conn) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT id, veiculo_id, inicio, kwh, duracao_s, potencia_max_w, potencia_media_w, curva_json "
        "FROM sessao WHERE status IN ('concluida', 'incompleta')", conn)
    inicio = pd.to_datetime(df["inicio"])
    curvas = df["curva_json"].apply(json.loads)
    df["duracao_h"] = df["duracao_s"] / 3600
    df["pot_media_kw"] = df["potencia_media_w"] / 1000
    df["pot_max_kw"] = df["potencia_max_w"] / 1000
    df["cv_curva"] = curvas.apply(lambda c: float(np.std(c) / np.mean(c)))
    esperado = df["pot_media_kw"] * df["duracao_h"]
    df["razao_energia_curva"] = df["kwh"] / esperado.replace(0, np.nan)
    hora = inicio.dt.hour + inicio.dt.minute / 60
    df["hora"] = hora
    df["hora_sin"], df["hora_cos"] = np.sin(2 * np.pi * hora / 24), np.cos(2 * np.pi * hora / 24)
    df["dia_semana"] = inicio.dt.weekday

    # comparação com o histórico do próprio veículo (mediana e MAD, robustos a outliers)
    g = df.groupby("veiculo_id")
    med_kwh, mad_kwh = g["kwh"].transform("median"), g["kwh"].transform(lambda s: (s - s.median()).abs().median())
    df["z_kwh_veiculo"] = (df["kwh"] - med_kwh) / (1.4826 * mad_kwh.clip(lower=0.5))
    med_hora = g["hora"].transform("median")
    diff = (df["hora"] - med_hora).abs()
    df["desvio_hora_veiculo"] = np.minimum(diff, 24 - diff)
    return df.fillna(df[FEATURES_ANOMALIA].median(numeric_only=True))


def detectar_anomalias(conn, contaminacao: float = 0.04, semente: int = 42) -> dict:
    df = _montar_features(conn)
    X = df[FEATURES_ANOMALIA]
    modelo = IsolationForest(n_estimators=300, contamination=contaminacao, random_state=semente)
    modelo.fit(X)
    df["score"] = -modelo.score_samples(X)          # maior = mais anômala
    df["sinalizada"] = (modelo.predict(X) == -1).astype(int)

    # explicação simples: a variável mais distante da média, em desvios-padrão (z-score).
    # Horário (seno/cosseno) é representado por "desvio_hora_veiculo", mais fácil de explicar.
    explicaveis = [c for c in FEATURES_ANOMALIA if c not in ("hora_sin", "hora_cos", "dia_semana")]
    z = ((X[explicaveis] - X[explicaveis].mean()) / X[explicaveis].std().replace(0, 1e-9)).abs()
    df["motivo"] = z.idxmax(axis=1).map(ROTULOS_LEGIVEIS)

    conn.execute("DELETE FROM anomalia")
    conn.executemany(
        "INSERT INTO anomalia(sessao_id, score, sinalizada, motivo) VALUES (?,?,?,?)",
        [(int(r.id), float(r.score), int(r.sinalizada), r.motivo if r.sinalizada else None)
         for r in df.itertuples()])
    conn.commit()
    return {"sessoes_analisadas": len(df), "sinalizadas": int(df["sinalizada"].sum())}


def avaliar_anomalias(conn) -> dict:
    """Compara com os rótulos simulados. Só faz sentido com dados sintéticos."""
    df = pd.read_sql_query(
        "SELECT s.rotulo_sim AS rotulo, a.sinalizada FROM sessao s JOIN anomalia a ON a.sessao_id = s.id", conn)
    injetadas = df["rotulo"].isin(["fraude", "falha", "medidor"])
    normais = df["rotulo"].isin(["normal"])
    por_tipo = {t: {"total": int((df["rotulo"] == t).sum()),
                    "detectadas": int(df.loc[df["rotulo"] == t, "sinalizada"].sum())}
                for t in ["fraude", "falha", "medidor", "incompleta"]}
    sinal_injetadas = int(df.loc[injetadas, "sinalizada"].sum())
    return {
        "por_tipo": por_tipo,
        "recall_injetadas": sinal_injetadas / max(1, int(injetadas.sum())),
        "falsos_positivos_normais": int(df.loc[normais, "sinalizada"].sum()),
        "total_normais": int(normais.sum()),
    }


# ---------------------------------------------------------------- demanda
def _serie_horaria(conn) -> pd.DataFrame:
    sess = pd.read_sql_query(
        "SELECT s.inicio, s.duracao_s, s.kwh FROM sessao s LEFT JOIN anomalia a ON a.sessao_id = s.id "
        "WHERE s.status IN ('concluida','incompleta') AND COALESCE(a.sinalizada, 0) = 0", conn)
    sess["inicio"] = pd.to_datetime(sess["inicio"])
    carga = {}
    for r in sess.itertuples():  # distribui a energia da sessão uniformemente pelas horas em que ocorreu
        fim = r.inicio + timedelta(seconds=int(r.duracao_s))
        h = r.inicio.floor("h")
        while h < fim:
            trecho = (min(fim, h + timedelta(hours=1)) - max(r.inicio, h)).total_seconds()
            carga[h] = carga.get(h, 0.0) + r.kwh * trecho / max(1, r.duracao_s)
            h += timedelta(hours=1)
    idx = pd.date_range(min(carga), max(carga), freq="h")
    serie = pd.DataFrame({"kwh": pd.Series(carga).reindex(idx, fill_value=0.0)})
    serie["hora"], serie["dia_semana"] = serie.index.hour, serie.index.weekday
    serie["feriado"] = [int(t.date() in FERIADOS) for t in serie.index]
    return serie


def _X_linear(df):
    return pd.concat([pd.get_dummies(df["hora"].astype(pd.CategoricalDtype(range(24))), prefix="h"),
                      pd.get_dummies(df["dia_semana"].astype(pd.CategoricalDtype(range(7))), prefix="d"),
                      df[["feriado"]]], axis=1).astype(float)


def _X_xgb(df):
    return df[["hora", "dia_semana", "feriado"]]


def treinar_demanda(conn, dias_teste: int = 21, semente: int = 42) -> dict:
    serie = _serie_horaria(conn)
    corte = serie.index.max() - pd.Timedelta(days=dias_teste)
    treino, teste = serie[serie.index <= corte], serie[serie.index > corte]

    media_hora_semana = treino.groupby(["dia_semana", "hora"])["kwh"].mean()
    pred_base = [media_hora_semana.get((d, h), 0.0) for d, h in zip(teste["dia_semana"], teste["hora"])]
    lin = LinearRegression().fit(_X_linear(treino), treino["kwh"])
    xgb = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.9,
                       random_state=semente).fit(_X_xgb(treino), treino["kwh"])
    metricas = {
        "media_por_hora_da_semana": mean_absolute_error(teste["kwh"], pred_base),
        "regressao_linear": mean_absolute_error(teste["kwh"], lin.predict(_X_linear(teste)).clip(0)),
        "xgboost": mean_absolute_error(teste["kwh"], xgb.predict(_X_xgb(teste)).clip(0)),
    }
    escolhido = min(["regressao_linear", "xgboost"], key=metricas.get)

    # reajusta o modelo escolhido com todo o histórico e grava a semana de referência (sem feriado)
    ref = pd.DataFrame([(d, h, 0) for d in range(7) for h in range(24)], columns=["dia_semana", "hora", "feriado"])
    if escolhido == "regressao_linear":
        previsto = LinearRegression().fit(_X_linear(serie), serie["kwh"]).predict(_X_linear(ref))
    else:
        previsto = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.9,
                                random_state=semente).fit(_X_xgb(serie), serie["kwh"]).predict(_X_xgb(ref))
    ref["kwh_previsto"] = np.clip(previsto, 0, None)
    conn.execute("DELETE FROM previsao_demanda")
    conn.executemany("INSERT INTO previsao_demanda(dia_semana, hora, kwh_previsto, modelo) VALUES (?,?,?,?)",
                     [(int(r.dia_semana), int(r.hora), float(r.kwh_previsto), escolhido) for r in ref.itertuples()])
    conn.commit()
    return {"mae_kwh_por_hora": {k: round(v, 3) for k, v in metricas.items()}, "modelo_escolhido": escolhido,
            "horas_treino": len(treino), "horas_teste": len(teste)}


def sugerir_horarios(conn, dia_semana: int, hora_min: int = 6, hora_max: int = 23, n: int = 3) -> list[dict]:
    """Horários de menor demanda prevista para o dia da semana (0 = segunda)."""
    linhas = conn.execute(
        "SELECT hora, kwh_previsto FROM previsao_demanda WHERE dia_semana = ? AND hora BETWEEN ? AND ? "
        "ORDER BY kwh_previsto ASC, hora ASC LIMIT ?", (dia_semana, hora_min, hora_max, n)).fetchall()
    return [{"hora": f"{r['hora']:02d}:00", "kwh_previsto": round(r["kwh_previsto"], 2)} for r in linhas]
