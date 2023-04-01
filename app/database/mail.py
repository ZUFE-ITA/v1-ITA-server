from fastapi_mail import ConnectionConfig
import random

from .includes import *
from .user import User
from ..utils.token_utils import hash_psw

class TeamMail:
    
    collection = db.team_mail

    
    @classmethod
    async def get_config(cls, team=None):
        if team is not None:
            rec = cls.collection.find_one({"team": team})
            if rec:
                return ConnectionConfig(
                    MAIL_USERNAME = rec['username'],
                    MAIL_PASSWORD = rec['password'],
                    MAIL_FROM     = rec['from'],
                    MAIL_PORT     = rec['port'],
                    MAIL_SERVER   = rec['server'],
                    MAIL_STARTTLS = False,
                    MAIL_SSL_TLS  = True,
                    USE_CREDENTIALS = True,
                    VALIDATE_CERTS  = True
                )
        default_record = await cls.collection.find_one({"default": True})
        default_config = ConnectionConfig(
            MAIL_USERNAME = default_record['from'],
            MAIL_PASSWORD = default_record['password'],
            MAIL_FROM = default_record['from'],
            MAIL_PORT = default_record['port'],
            MAIL_SERVER = default_record['host'],
            MAIL_STARTTLS = False,
            MAIL_SSL_TLS = True,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True
        )
        return default_config

class VerifyMail:
    """ redis db """

    @classmethod
    async def generate(cls, uid: str, code_type, cd: int, expire: int = 1800, length: int = 6):
        # 检查距离上次发有没有过去cd时间
        ttl = r.ttl_verify_code(uid, code_type)
        if ttl > 0 and expire - ttl < cd:
            # 不到一分钟
            s = cd - expire + ttl
            raise ServiceException(
                status.HTTP_403_FORBIDDEN,
                detail=f"请{s}秒后再尝试",
                code = ErrorCode.FORM.TRY_AGAIN_AFTER_,
                s = s
            )
        code = ''
        while len(code) < length:
            code += str(random.randint(0, 9))
        r.set_verify_code(uid, code, code_type, expire)
        return code

    @classmethod
    async def verify(cls, uid: str, code: int, code_type):
        if raw := r.get_verify_code(uid, code_type):
            if raw == str(code):
                # 更新状态
                return True
            raise ServiceException(
                status.HTTP_400_BAD_REQUEST,
                detail="验证码不正确",
                code = ErrorCode.FORM.CODE_WRONG
            )
        raise ServiceException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="code not found",
            code = ErrorCode.FORM.CODE_EXPIRED
        )


"""邮箱激活"""
async def gen_activate_code(uid, cd = 60):
    return await VerifyMail.generate(uid, "activate", cd)

async def verify_activate_code(uid, code):
    if await VerifyMail.verify(uid, code, "activate"):
        return await User.update_info(uid, {"activated": True})

"""忘记密码"""
async def gen_reset_psw_code(uid, cd=60):
    return await VerifyMail.generate(uid, "reset_psw", cd)

async def verify_reset_psw_code(uid, code, new_psw: str):
    if await VerifyMail.verify(uid, code, "reset_psw"):
        psw = hash_psw(new_psw)
        return await User.update_info(uid, {"psw": psw})
