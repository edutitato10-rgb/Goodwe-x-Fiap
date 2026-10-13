"""Dados simulados para validar o pipeline (3 meses de uso de um condomínio fictício).

Os dados são sintéticos e determinísticos (semente fixa). Algumas sessões recebem
anomalias injetadas (fraude, falha do carregador, erro de medidor) e o campo
`rotulo_sim` guarda a verdade apenas para avaliar a IA; o módulo de IA não lê esse campo.
"""
import json
from datetime import date, datetime, timedelta

import numpy as np

from .db import definir_parametro
from .seguranca import hash_senha

SEMENTE = 42
INICIO = date(2026, 7, 1)
FIM = date(2026, 9, 30)
FERIADOS = {date(2026, 9, 7)}
POTENCIA_MAX_W = 7400.0
PASSO_CURVA_S = 900  # 15 min

NOMES = ["Ana Souza", "Bruno Lima", "Carla Mendes", "Diego Alves", "Elisa Rocha", "Fábio Costa",
         "Gabriela Dias", "Hugo Martins", "Isabela Nunes", "João Pereira", "Karina Teixeira",
         "Leandro Ramos"]
MODELOS = ["BYD Dolphin", "Renault Kwid E-Tech", "GWM Ora 03", "Volvo EX30", "BMW iX1", "BYD Seal"]

PESO_UTIL = np.array([1, 1, 1, 1, 1, 2, 4, 5, 3, 1, 1, 1, 2, 2, 1, 1, 2, 4, 9, 12, 10, 7, 3, 2], float)
PESO_FDS = np.array([1, 1, 1, 1, 1, 1, 2, 3, 4, 6, 8, 9, 8, 7, 6, 5, 5, 6, 8, 8, 6, 4, 2, 1], float)


def _curva(rng, duracao_s: int, pmax: float, modo: str = "normal") -> list[float]:
    n = max(2, int(np.ceil(duracao_s / PASSO_CURVA_S)))
    base = np.full(n, pmax * rng.uniform(0.88, 0.97))
    cauda = max(1, int(n * 0.2))
    base[-cauda:] *= np.linspace(1.0, 0.45, cauda)  # redução de potência no fim da carga
    if modo == "falha":  # degradação progressiva ao longo da sessão
        base = np.linspace(pmax * 0.9, pmax * 0.2, n)
    ruido = rng.normal(0, pmax * 0.015, n)
    return [float(max(300.0, v)) for v in base + ruido]


def _energia_kwh(curva) -> float:
    return sum(curva) * PASSO_CURVA_S / 3600 / 1000


def popular(conn) -> dict:
    rng = np.random.default_rng(SEMENTE)
    senha = hash_senha("senha123")

    conn.execute("INSERT INTO usuario(nome, email, senha_hash, papel, ativo) VALUES (?,?,?,?,0)",
                 ("Síndico", "sindico@condominio.test", senha, "gestor"))
    definir_parametro(conn, "tarifa_kwh", 0.95)
    definir_parametro(conn, "custo_fixo_mensal", 300.0)
    definir_parametro(conn, "cobrar_fixo_sem_recarga", 1.0)

    veiculos = []  # (veiculo_id, usuario_id, rfid, sessoes_por_semana, hora_pref)
    contador_rfid = 0
    for i, nome in enumerate(NOMES, start=1):
        cur = conn.execute("INSERT INTO unidade(identificacao) VALUES (?)", (f"Apto {100 + i}",))
        uid_un = cur.lastrowid
        cur = conn.execute(
            "INSERT INTO usuario(nome, email, senha_hash, papel, unidade_id, ativo) "
            "VALUES (?,?,?,?,?,1)",
            (nome, f"morador{i}@condominio.test", senha, "morador", uid_un))
        uid = cur.lastrowid
        n_veic = 2 if i in (3, 7) else 1  # duas unidades com dois veículos
        for k in range(n_veic):
            contador_rfid += 1
            rfid = f"UID-{contador_rfid:08X}"
            cur = conn.execute("INSERT INTO veiculo(usuario_id, placa, modelo, rfid) VALUES (?,?,?,?)",
                               (uid, f"EVC{i}{k}A{contador_rfid % 10}", MODELOS[(i + k) % len(MODELOS)], rfid))
            freq = 0.0 if i == 12 else float(rng.uniform(1.5, 4.5))  # usuário 12 nunca recarrega
            veiculos.append((cur.lastrowid, uid, rfid, freq, int(rng.integers(0, 3))))
    conn.commit()

    sessoes = []
    dias = (FIM - INICIO).days + 1
    for vid, uid, rfid, freq, _ in veiculos:
        kwh_tipico = float(rng.uniform(8, 18))
        for d in range(dias):
            dia = INICIO + timedelta(days=d)
            fim_semana = dia.weekday() >= 5 or dia in FERIADOS
            if rng.random() > freq / 7:
                continue
            pesos = PESO_FDS if fim_semana else PESO_UTIL
            hora = int(rng.choice(24, p=pesos / pesos.sum()))
            inicio = datetime(dia.year, dia.month, dia.day, hora, int(rng.integers(0, 60)))
            kwh_desejado = float(np.clip(rng.normal(kwh_tipico, 3), 4, 30))
            duracao_s = int(kwh_desejado / (POTENCIA_MAX_W * 0.9 / 1000) * 3600)
            curva = _curva(rng, duracao_s, POTENCIA_MAX_W)
            sessoes.append(dict(vid=vid, rfid=rfid, inicio=inicio, duracao_s=duracao_s,
                                curva=curva, kwh=_energia_kwh(curva), status="concluida", rotulo="normal"))

    # sessões interrompidas (consumo parcial, faturado normalmente)
    for idx in rng.choice(len(sessoes), 10, replace=False):
        s = sessoes[idx]
        corte = max(2, int(len(s["curva"]) * rng.uniform(0.25, 0.7)))
        s["curva"] = s["curva"][:corte]
        s["duracao_s"] = corte * PASSO_CURVA_S
        s["kwh"] = _energia_kwh(s["curva"])
        s["status"], s["rotulo"] = "incompleta", "incompleta"

    # anomalias injetadas ------------------------------------------------------------
    normais = [i for i, s in enumerate(sessoes) if s["rotulo"] == "normal"]
    # fraude: tag usada de madrugada com consumo muito acima do padrão do veículo
    for idx in rng.choice(normais, 8, replace=False):
        s = sessoes[idx]
        dur = int(rng.uniform(4.5, 6.0) * 3600)
        s["inicio"] = s["inicio"].replace(hour=int(rng.integers(2, 5)))
        s["duracao_s"], s["curva"] = dur, _curva(rng, dur, POTENCIA_MAX_W)
        s["kwh"], s["rotulo"] = _energia_kwh(s["curva"]), "fraude"
    normais = [i for i in normais if sessoes[i]["rotulo"] == "normal"]
    # falha do carregador: potência degradando durante a sessão
    for idx in rng.choice(normais, 6, replace=False):
        s = sessoes[idx]
        dur = int(rng.uniform(3.0, 5.0) * 3600)
        s["duracao_s"], s["curva"] = dur, _curva(rng, dur, POTENCIA_MAX_W, "falha")
        s["kwh"], s["rotulo"] = _energia_kwh(s["curva"]), "falha"
    normais = [i for i in normais if sessoes[i]["rotulo"] == "normal"]
    # erro de medidor: energia reportada incompatível com a curva de potência
    for idx in rng.choice(normais, 5, replace=False):
        s = sessoes[idx]
        s["kwh"], s["rotulo"] = s["kwh"] * float(rng.uniform(2.2, 3.0)), "medidor"

    sessoes.sort(key=lambda s: s["inicio"])
    for s in sessoes:
        fim = s["inicio"] + timedelta(seconds=s["duracao_s"])
        conn.execute(
            """INSERT INTO sessao(veiculo_id, rfid, inicio, fim, kwh, duracao_s, potencia_max_w,
                                  potencia_media_w, curva_json, status, rotulo_sim)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (s["vid"], s["rfid"], s["inicio"].strftime("%Y-%m-%d %H:%M:%S"),
             fim.strftime("%Y-%m-%d %H:%M:%S"), round(s["kwh"], 3), s["duracao_s"],
             max(s["curva"]), sum(s["curva"]) / len(s["curva"]), json.dumps([round(p, 1) for p in s["curva"]]),
             s["status"], s["rotulo"]))
    conn.commit()
    return {"usuarios": len(NOMES), "veiculos": len(veiculos), "sessoes": len(sessoes)}
