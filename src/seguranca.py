"""Hash de senha (PBKDF2) e tokens JWT para a API."""
import hashlib
import hmac
import os
import time

import jwt

SEGREDO = os.environ.get("EVCHARGEOPS_JWT_SECRET", "troque-este-segredo-em-producao")
VALIDADE_S = 3600


def hash_senha(senha: str, sal: bytes | None = None) -> str:
    sal = sal or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, 100_000)
    return sal.hex() + "$" + dk.hex()


def verificar_senha(senha: str, armazenado: str) -> bool:
    sal_hex, dk_hex = armazenado.split("$")
    esperado = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal_hex), 100_000)
    return hmac.compare_digest(esperado.hex(), dk_hex)


def criar_token(usuario_id: int, papel: str) -> str:
    agora = int(time.time())
    return jwt.encode({"sub": str(usuario_id), "papel": papel, "iat": agora, "exp": agora + VALIDADE_S},
                      SEGREDO, algorithm="HS256")


def ler_token(token: str) -> dict:
    return jwt.decode(token, SEGREDO, algorithms=["HS256"])
