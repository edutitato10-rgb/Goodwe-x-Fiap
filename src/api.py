"""API REST (FastAPI) com autenticação JWT. Consumida pelo app Flutter e pelo dashboard web."""
import json
import sqlite3
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from . import db, ia, rateio, seguranca

app = FastAPI(title="EV ChargeOps API", version="0.2.0")


def get_conn():
    conn = db.conectar()
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


class Login(BaseModel):
    email: str
    senha: str


def usuario_atual(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    try:
        dados = seguranca.ler_token(authorization.removeprefix("Bearer "))
    except jwt.PyJWTError:
        raise HTTPException(401, "Token inválido ou expirado")
    return {"id": int(dados["sub"]), "papel": dados["papel"]}


Usuario = Annotated[dict, Depends(usuario_atual)]


def exigir_gestor(u: Usuario) -> dict:
    if u["papel"] != "gestor":
        raise HTTPException(403, "Acesso restrito ao gestor")
    return u


@app.post("/auth/login")
def login(corpo: Login, conn: Conn):
    u = conn.execute("SELECT id, senha_hash, papel FROM usuario WHERE email = ?", (corpo.email,)).fetchone()
    if u is None or not seguranca.verificar_senha(corpo.senha, u["senha_hash"]):
        raise HTTPException(401, "Credenciais inválidas")
    return {"access_token": seguranca.criar_token(u["id"], u["papel"]), "token_type": "bearer", "papel": u["papel"]}


@app.get("/minhas/sessoes")
def minhas_sessoes(u: Usuario, conn: Conn, limite: int = 20):
    linhas = conn.execute(
        "SELECT s.id, v.placa, s.inicio, s.fim, s.kwh, s.status FROM sessao s JOIN veiculo v ON v.id = s.veiculo_id "
        "WHERE v.usuario_id = ? ORDER BY s.inicio DESC LIMIT ?", (u["id"], limite)).fetchall()
    return [dict(l) for l in linhas]


@app.get("/minhas/faturas/{mes}")
def minha_fatura(mes: str, u: Usuario, conn: Conn):
    f = conn.execute("SELECT * FROM fatura WHERE usuario_id = ? AND mes = ?", (u["id"], mes)).fetchone()
    if f is None:
        raise HTTPException(404, "Fatura não encontrada")
    d = dict(f)
    d["detalhe"] = json.loads(d.pop("detalhe_json"))
    return d


@app.get("/sugestao-horarios")
def sugestao(dia_semana: int, u: Usuario, conn: Conn):
    if not 0 <= dia_semana <= 6:
        raise HTTPException(422, "dia_semana deve estar entre 0 (segunda) e 6 (domingo)")
    return ia.sugerir_horarios(conn, dia_semana)


@app.get("/gestor/faturas/{mes}")
def faturas_do_mes(mes: str, conn: Conn, _: Annotated[dict, Depends(exigir_gestor)]):
    return rateio.calcular_faturas(conn, mes, persistir=False)


@app.get("/gestor/anomalias")
def anomalias(conn: Conn, _: Annotated[dict, Depends(exigir_gestor)]):
    linhas = conn.execute(
        "SELECT s.id AS sessao_id, v.placa, s.inicio, s.kwh, s.status, a.score, a.motivo FROM anomalia a "
        "JOIN sessao s ON s.id = a.sessao_id JOIN veiculo v ON v.id = s.veiculo_id "
        "WHERE a.sinalizada = 1 ORDER BY a.score DESC").fetchall()
    return [dict(l) for l in linhas]
