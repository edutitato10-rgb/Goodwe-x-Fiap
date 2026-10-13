"""Integração com a API SEMS da GoodWe (Sprint 1, seção 2.3).

- SemsClient: cliente real (CrossLogin + polling). Exige credenciais de uma conta SEMS.
- SemsSimulado: gera payloads no mesmo formato JSON, para demonstrar a ingestão sem hardware.
- processar_payload: transforma cada resposta em registro de sessão, vinculado por rfidCard.
"""
import json
from datetime import datetime, timedelta, timezone

import requests

URL_LOGIN = "https://www.semsportal.com/api/v1/Common/CrossLogin"
ENDPOINT_CARGA = "/api/v3/EvCharger/GetCurrentChargeinfo"
FUSO_LOCAL = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horário de verão)

INATIVO, CONECTADO, CARREGANDO, ERRO = 0, 1, 2, 3


class SemsClient:
    def __init__(self, email: str, senha: str):
        self.email, self.senha = email, senha
        self.token = None
        self.base = None

    def login(self) -> None:
        cabecalho = {"Token": json.dumps({"version": "v2.1.0", "client": "ios", "language": "en"})}
        r = requests.post(URL_LOGIN, headers=cabecalho,
                          json={"account": self.email, "pwd": self.senha}, timeout=15)
        r.raise_for_status()
        corpo = r.json()
        self.token = json.dumps(corpo["data"])
        self.base = corpo["api"].rstrip("/")

    def consultar(self, station_id: str) -> dict:
        if not self.token:
            self.login()
        r = requests.post(self.base + ENDPOINT_CARGA, headers={"Token": self.token},
                          json={"stationId": station_id}, timeout=15)
        r.raise_for_status()
        return r.json()


class SemsSimulado:
    """Reproduz a estrutura do JSON documentado na Sprint 1 para uma sessão de recarga."""

    def __init__(self, rfid: str, inicio_utc: datetime, kwh_alvo: float = 10.0,
                 potencia_w: int = 7400, falhar_em: int | None = None):
        self.rfid, self.inicio = rfid, inicio_utc
        self.kwh_alvo, self.potencia_w, self.falhar_em = kwh_alvo, potencia_w, falhar_em

    def sequencia(self, passo_s: int = 60):
        """Gera as respostas de polling: conectado -> carregando... -> encerrado (ou erro)."""
        yield self._payload(CONECTADO, 0, 0.0, 0)
        t, energia, n = 0, 0.0, 0
        while energia < self.kwh_alvo:
            t += passo_s
            n += 1
            energia = min(self.kwh_alvo, energia + self.potencia_w * passo_s / 3_600_000)
            if self.falhar_em is not None and n >= self.falhar_em:
                yield self._payload(ERRO, t, energia, 0)
                return
            yield self._payload(CARREGANDO, t, energia, self.potencia_w)
        yield self._payload(INATIVO, t, energia, 0)

    def _payload(self, status, duracao, energia, potencia):
        return {"code": 0, "msg": "success", "data": {
            "stationId": "simulado-0001", "evChargerStatus": status, "power": potencia,
            "energy": round(energia, 3),
            "sessionStartTime": self.inicio.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sessionEndTime": None, "duration": duracao, "rfidCard": self.rfid,
            "voltage": 231.4, "maxPower": 7400, "temperature": 38.2}}


def _para_local(iso_utc: str) -> str:
    dt = datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(FUSO_LOCAL).strftime("%Y-%m-%d %H:%M:%S")


def processar_payload(conn, payload: dict) -> str | None:
    """Aplica uma leitura do SEMS ao banco. Retorna o evento ocorrido ('aberta', 'atualizada',
    'concluida', 'incompleta') ou None se a leitura foi ignorada."""
    if payload.get("code") != 0:
        return None
    d = payload["data"]
    rfid, status = d.get("rfidCard"), d["evChargerStatus"]
    if not rfid:
        return None

    veiculo = conn.execute("SELECT id FROM veiculo WHERE rfid = ?", (rfid,)).fetchone()
    if veiculo is None:  # cartão não cadastrado: não gera sessão faturável
        return None

    aberta = conn.execute(
        "SELECT id, curva_json FROM sessao WHERE rfid = ? AND status = 'em_andamento'", (rfid,)
    ).fetchone()

    if status == CARREGANDO:
        if aberta is None:
            conn.execute(
                "INSERT INTO sessao(veiculo_id, rfid, inicio, kwh, duracao_s, status, curva_json) "
                "VALUES (?, ?, ?, ?, ?, 'em_andamento', ?)",
                (veiculo["id"], rfid, _para_local(d["sessionStartTime"]), d["energy"],
                 d["duration"], json.dumps([d["power"]])))
            conn.commit()
            return "aberta"
        curva = json.loads(aberta["curva_json"] or "[]") + [d["power"]]
        conn.execute("UPDATE sessao SET kwh = ?, duracao_s = ?, curva_json = ? WHERE id = ?",
                     (d["energy"], d["duration"], json.dumps(curva), aberta["id"]))
        conn.commit()
        return "atualizada"

    if aberta is None:
        return None

    # Status 0/1 encerra normalmente; status 3 (erro) encerra como incompleta (último checkpoint).
    curva = json.loads(aberta["curva_json"] or "[]") or [d["power"]]
    final = "incompleta" if status == ERRO else "concluida"
    inicio = conn.execute("SELECT inicio FROM sessao WHERE id = ?", (aberta["id"],)).fetchone()["inicio"]
    fim = (datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=d["duration"])
           ).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE sessao SET kwh = ?, duracao_s = ?, fim = ?, status = ?, potencia_max_w = ?, "
        "potencia_media_w = ? WHERE id = ?",
        (d["energy"], d["duration"], fim, final, max(curva), sum(curva) / len(curva), aberta["id"]))
    conn.commit()
    return final
