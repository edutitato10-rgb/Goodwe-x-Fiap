"""Motor de rateio (Sprint 1, seção 3.3).

Fatura_usuario = (kWh_usuario x Tarifa_energia) + (Custo_fixo_manutencao / N_usuarios_ativos)

Exceções tratadas:
  1. Sessão interrompida: o kWh do último checkpoint já está em sessao.kwh; a sessão é
     faturada normalmente e fica com status 'incompleta' para auditoria.
  2. Usuário sem recarga: variável = 0, mas paga a parcela fixa (parametrizável).
  3. Unidade com dois veículos: kWh dos veículos do mesmo usuário são somados em uma
     fatura consolidada, com detalhamento por veículo.
"""
import json

from .db import obter_parametro

STATUS_FATURAVEIS = ("concluida", "incompleta")


def calcular_faturas(conn, mes: str, persistir: bool = True) -> list[dict]:
    """Calcula as faturas de todos os usuários ativos para o mês 'YYYY-MM'."""
    tarifa = obter_parametro(conn, "tarifa_kwh")
    custo_fixo = obter_parametro(conn, "custo_fixo_mensal")
    cobra_fixo_sem_uso = bool(obter_parametro(conn, "cobrar_fixo_sem_recarga"))

    usuarios = conn.execute(
        "SELECT id, nome, unidade_id FROM usuario WHERE ativo = 1 AND papel = 'morador' ORDER BY id"
    ).fetchall()
    n_ativos = len(usuarios)
    if n_ativos == 0:
        return []
    fixo_por_usuario = custo_fixo / n_ativos

    faturas = []
    for u in usuarios:
        linhas = conn.execute(
            """
            SELECT v.placa, COUNT(s.id) AS sessoes, COALESCE(SUM(s.kwh), 0) AS kwh,
                   COALESCE(SUM(s.status = 'incompleta'), 0) AS incompletas
            FROM veiculo v
            LEFT JOIN sessao s ON s.veiculo_id = v.id
                 AND substr(s.inicio, 1, 7) = ?
                 AND s.status IN ('concluida', 'incompleta')
            WHERE v.usuario_id = ?
            GROUP BY v.id ORDER BY v.id
            """,
            (mes, u["id"]),
        ).fetchall()

        detalhe = {
            l["placa"]: {
                "sessoes": l["sessoes"],
                "kwh": round(l["kwh"], 3),
                "valor_variavel": round(l["kwh"] * tarifa, 2),
                "sessoes_incompletas": l["incompletas"],
            }
            for l in linhas
        }
        kwh_total = sum(l["kwh"] for l in linhas)
        variavel = round(kwh_total * tarifa, 2)
        fixo = round(fixo_por_usuario, 2) if (kwh_total > 0 or cobra_fixo_sem_uso) else 0.0
        faturas.append({
            "usuario_id": u["id"],
            "nome": u["nome"],
            "mes": mes,
            "kwh_total": round(kwh_total, 3),
            "valor_variavel": variavel,
            "valor_fixo": fixo,
            "valor_total": round(variavel + fixo, 2),
            "detalhe": detalhe,
        })

    if persistir:
        for f in faturas:
            conn.execute(
                """INSERT INTO fatura(usuario_id, mes, kwh_total, valor_variavel, valor_fixo,
                                      valor_total, detalhe_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(usuario_id, mes) DO UPDATE SET
                     kwh_total = excluded.kwh_total, valor_variavel = excluded.valor_variavel,
                     valor_fixo = excluded.valor_fixo, valor_total = excluded.valor_total,
                     detalhe_json = excluded.detalhe_json""",
                (f["usuario_id"], f["mes"], f["kwh_total"], f["valor_variavel"], f["valor_fixo"],
                 f["valor_total"], json.dumps(f["detalhe"], ensure_ascii=False)),
            )
        conn.commit()
    return faturas


def estimar_custo(conn, kwh: float) -> float:
    """Custo estimado exibido antes da sessão (transparência tarifária, RN ANEEL 1.000/2021)."""
    return round(kwh * obter_parametro(conn, "tarifa_kwh"), 2)
