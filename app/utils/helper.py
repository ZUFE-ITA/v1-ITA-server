from fastapi import Response
import bcrypt

def set_cookie(resp: Response, key: str, value: str, max_age: int | None = None,
        expires: int | None = None, path: str = "/", domain: str | None = None):
    resp.set_cookie(key, value, max_age=max_age, expires=expires, path=path, domain=domain, httponly=True, samesite='none', secure=True)

def hash_psw(psw: str):
    origin_psw = psw.encode('utf8')
    psw = bcrypt.hashpw(origin_psw, bcrypt.gensalt())
    return psw