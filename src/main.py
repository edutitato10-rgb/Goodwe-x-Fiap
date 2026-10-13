"""Executa o pipeline completo e gera as evidências em evidencias/."""
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from . import db, ia, rateio, seed
from .sems_client import SemsSimulado, processar_payload

RAIZ = Path(__file__).resolve().parent.parent
EVID = RAIZ / "evidencias"
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def titulo(texto):
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)


def demonstrar_ingestao(conn):
    titulo("2. Ingestão SEMS (simulada): polling de uma sessão completa e de uma interrompida")
    rfid = conn.execute("SELECT rfid FROM veiculo ORDER BY id LIMIT 1").fetchone()["rfid"]
    for nome, sim in [("sessão normal", SemsSimulado(rfid, datetime(2026, 10, 1, 21, 0, tzinfo=timezone.utc), 9.0)),
                      ("sessão com erro do carregador", SemsSimulado(rfid, datetime(2026, 10, 2, 21, 0, tzinfo=timezone.utc),
                                                                      9.0, falhar_em=30))]:
        eventos = [processar_payload(conn, p) for p in sim.sequencia(passo_s=60)]
        s = conn.execute("SELECT id, inicio, kwh, duracao_s, status FROM sessao ORDER BY id DESC LIMIT 1").fetchone()
        print(f"- {nome}: {len(eventos)} leituras -> sessão {s['id']} | início {s['inicio']} (horário local) | "
              f"{s['kwh']:.2f} kWh | {s['duracao_s'] // 60} min | status={s['status']}")
    r = processar_payload(conn, {"code": 0, "data": {"evChargerStatus": 2, "power": 7400, "energy": 1.0,
                                 "sessionStartTime": "2026-10-03T10:00:00Z", "duration": 60, "rfidCard": "UID-DESCONHECIDO"}})
    print(f"- cartão não cadastrado: leitura ignorada (retorno={r})")


def graficos(conn):
    df = pd.read_sql_query(
        "SELECT s.kwh, s.duracao_s/3600.0 AS dur_h, s.rotulo_sim, a.sinalizada FROM sessao s "
        "JOIN anomalia a ON a.sessao_id = s.id", conn)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ok = df[df["sinalizada"] == 0]
    ax.scatter(ok["dur_h"], ok["kwh"], s=12, alpha=.5, label="normal")
    fl = df[df["sinalizada"] == 1]
    ax.scatter(fl["dur_h"], fl["kwh"], s=40, c="crimson", marker="x", label="sinalizada pela IA")
    ax.set(xlabel="duração (h)", ylabel="energia (kWh)", title="Isolation Forest: sessões sinalizadas")
    ax.legend(); fig.tight_layout(); fig.savefig(EVID / "anomalias.png", dpi=130); plt.close(fig)

    prev = pd.read_sql_query("SELECT * FROM previsao_demanda", conn)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for d, cor in [(2, "tab:blue"), (5, "tab:orange")]:
        p = prev[prev["dia_semana"] == d].sort_values("hora")
        ax.plot(p["hora"], p["kwh_previsto"], marker="o", ms=3, label=DIAS[d], color=cor)
    ax.set(xlabel="hora do dia", ylabel="kWh previstos por hora", title=f"Demanda prevista ({prev['modelo'].iloc[0]})")
    ax.legend(); fig.tight_layout(); fig.savefig(EVID / "previsao_demanda.png", dpi=130); plt.close(fig)


def main():
    EVID.mkdir(exist_ok=True)
    caminho = db.DB_PADRAO
    caminho.parent.mkdir(exist_ok=True)
    if caminho.exists():
        caminho.unlink()
    conn = db.conectar(caminho)

    titulo("1. Banco de dados e dados simulados")
    db.criar_esquema(conn)
    print("Resumo:", seed.popular(conn))

    demonstrar_ingestao(conn)

    titulo("3. Detecção de anomalias (Isolation Forest)")
    print(ia.detectar_anomalias(conn))
    av = ia.avaliar_anomalias(conn)
    print(json.dumps(av, indent=2, ensure_ascii=False))
    print("\nSessões sinalizadas (maior score primeiro):")
    top = pd.read_sql_query(
        "SELECT s.id, s.inicio, v.placa, round(s.kwh,1) AS kwh, round(s.duracao_s/3600.0,1) AS horas, "
        "round(a.score,3) AS score, a.motivo, s.rotulo_sim AS rotulo_simulado FROM anomalia a "
        "JOIN sessao s ON s.id = a.sessao_id JOIN veiculo v ON v.id = s.veiculo_id "
        "WHERE a.sinalizada = 1 ORDER BY a.score DESC LIMIT 12", conn)
    print(top.to_string(index=False))

    titulo("4. Previsão de demanda (Regressão Linear vs XGBoost)")
    res = ia.treinar_demanda(conn)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    for d in (2, 5):
        print(f"Melhores horários na {DIAS[d]}-feira: {ia.sugerir_horarios(conn, d)}" if d < 5
              else f"Melhores horários no {DIAS[d]}: {ia.sugerir_horarios(conn, d)}")

    titulo("5. Rateio mensal (setembro/2026)")
    faturas = rateio.calcular_faturas(conn, "2026-09")
    tab = pd.DataFrame([{k: f[k] for k in ("nome", "kwh_total", "valor_variavel", "valor_fixo", "valor_total")}
                        for f in faturas])
    print(tab.to_string(index=False))
    print(f"\nTotal faturado: R$ {tab['valor_total'].sum():.2f} | custo fixo previsto: R$ 300.00 | "
          f"energia medida: {tab['kwh_total'].sum():.1f} kWh")
    tab.to_csv(EVID / "faturas_2026-09.csv", index=False)
    for mes in ("2026-07", "2026-08"):
        rateio.calcular_faturas(conn, mes)

    graficos(conn)
    print(f"\nEvidências gravadas em {EVID}")


if __name__ == "__main__":
    main()
