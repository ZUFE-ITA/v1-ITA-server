from fastapi import Response
import bcrypt

from datetime import timedelta, datetime
from jose import jwt

from ..database import Config

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expire_delta: timedelta | None = None):
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    encode_jwt = jwt.encode(
        to_encode, Config.secret_key(), algorithm=ALGORITHM)
    return encode_jwt

def get_id_from_token(token: str):
    payload = jwt.decode(
        token, Config.secret_key(), algorithms=[ALGORITHM])
    id = payload.get("sub")
    return id

def generate_user_token(uid: str, age: int|None = None):
    to_encode = {"sub": uid}
    expire = timedelta(seconds=age) if age is not None else None
    access_token = create_access_token(to_encode, expire)
    return access_token


def set_cookie(resp: Response, key: str, value: str, max_age: int | None = None,
        expires: int | None = None, path: str = "/", domain: str | None = None):
    resp.set_cookie(key, value, max_age=max_age, expires=expires, path=path, domain=domain, httponly=True, samesite='none', secure=True)

def hash_psw(psw: str):
    origin_psw = psw.encode('utf8')
    psw = bcrypt.hashpw(origin_psw, bcrypt.gensalt())
    return psw
