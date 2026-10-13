from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src import api, db, rateio, seguranca
from src.sems_client import SemsSimulado, processar_payload


@pytest.fixture
def conn():
    c = db.conectar(":memory:")
    db.criar_esquema(c)
    db.definir_parametro(c, "tarifa_kwh", 1.0)
    db.definir_parametro(c, "custo_fixo_mensal", 90.0)
    db.definir_parametro(c, "cobrar_fixo_sem_recarga", 1.0)
    h = seguranca.hash_senha("x")
    for i in (1, 2, 3):
        c.execute("INSERT INTO usuario(id, nome, email, senha_hash, papel, ativo) VALUES (?,?,?,?,?,1)",
                  (i, f"U{i}", f"u{i}@t", h, "morador"))
    c.execute("INSERT INTO usuario(id, nome, email, senha_hash, papel, ativo) VALUES (9,'G','g@t',?,'gestor',0)", (h,))
    for vid, uid, rfid in [(1, 1, "R1"), (2, 2, "R2"), (3, 2, "R3"), (4, 3, "R4")]:
        c.execute("INSERT INTO veiculo(id, usuario_id, placa, rfid) VALUES (?,?,?,?)", (vid, uid, f"P{vid}", rfid))
    def sessao(vid, rfid, kwh, status):
        c.execute("INSERT INTO sessao(veiculo_id, rfid, inicio, kwh, duracao_s, status) VALUES (?,?,?,?,3600,?)",
                  (vid, rfid, "2026-09-10 20:00:00", kwh, status))
    sessao(1, "R1", 100, "concluida")
    sessao(2, "R2", 10, "concluida")
    sessao(3, "R3", 20, "incompleta")   # consumo parcial deve ser faturado
    sessao(3, "R3", 5, "em_andamento")  # sessão aberta não entra
    c.commit()
    return c


def test_rateio_formula_e_excecoes(conn):
    f = {x["usuario_id"]: x for x in rateio.calcular_faturas(conn, "2026-09")}
    assert f[1]["valor_total"] == 130.0          # 100 kWh + 30 fixo
    assert f[2]["kwh_total"] == 30.0             # dois veículos consolidados (10 + 20 incompleta)
    assert f[2]["valor_total"] == 60.0
    assert set(f[2]["detalhe"]) == {"P2", "P3"}  # detalhamento por veículo
    assert f[3]["valor_variavel"] == 0 and f[3]["valor_fixo"] == 30.0  # sem recarga paga só o fixo


def test_fixo_sem_recarga_parametrizavel(conn):
    db.definir_parametro(conn, "cobrar_fixo_sem_recarga", 0.0)
    f = {x["usuario_id"]: x for x in rateio.calcular_faturas(conn, "2026-09")}
    assert f[3]["valor_total"] == 0.0


def test_ingestao_sessao_completa_e_interrompida(conn):
    sim = SemsSimulado("R1", datetime(2026, 10, 1, 21, 0, tzinfo=timezone.utc), kwh_alvo=5.0)
    eventos = [processar_payload(conn, p) for p in sim.sequencia()]
    assert eventos[0] is None and eventos[1] == "aberta" and eventos[-1] == "concluida"
    s = conn.execute("SELECT * FROM sessao WHERE inicio LIKE '2026-10-01%'").fetchone()
    assert s["status"] == "concluida" and s["kwh"] == 5.0 and s["inicio"].endswith("18:00:00")

    sim = SemsSimulado("R4", datetime(2026, 10, 2, 21, 0, tzinfo=timezone.utc), kwh_alvo=5.0, falhar_em=10)
    eventos = [processar_payload(conn, p) for p in sim.sequencia()]
    assert eventos[-1] == "incompleta"


def test_cartao_desconhecido_nao_gera_sessao(conn):
    payload = {"code": 0, "data": {"evChargerStatus": 2, "power": 7400, "energy": 1, "duration": 60,
                                   "sessionStartTime": "2026-10-01T10:00:00Z", "rfidCard": "NAO-EXISTE"}}
    assert processar_payload(conn, payload) is None


def test_api_autenticacao_e_papeis(conn, tmp_path, monkeypatch):
    rateio.calcular_faturas(conn, "2026-09")
    arquivo = tmp_path / "t.db"
    destino = db.conectar(arquivo)
    conn.backup(destino)
    destino.close()
    original = db.conectar
    monkeypatch.setattr(db, "conectar", lambda caminho=arquivo: original(caminho))
    cli = TestClient(api.app)

    assert cli.get("/minhas/sessoes").status_code == 401
    assert cli.post("/auth/login", json={"email": "u1@t", "senha": "errada"}).status_code == 401
    tok = cli.post("/auth/login", json={"email": "u1@t", "senha": "x"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert cli.get("/minhas/faturas/2026-09", headers=h).json()["valor_total"] == 130.0
    assert cli.get("/gestor/anomalias", headers=h).status_code == 403
    tg = cli.post("/auth/login", json={"email": "g@t", "senha": "x"}).json()["access_token"]
    assert cli.get("/gestor/anomalias", headers={"Authorization": f"Bearer {tg}"}).status_code == 200
