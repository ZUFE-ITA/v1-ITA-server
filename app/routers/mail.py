from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from ..dependencies import UserInfo
from .. import dependencies
from ..database import  User, Article, gen_activate_code, gen_reset_psw_code, verify_activate_code, verify_reset_psw_code
from ..utils.mail import send_verify_code_mail
from ..utils.token import generate_user_token
from ..utils.helper import set_cookie
from ..utils.checker import check_psw
from ..exceptions import ServiceException, ErrorCode

router = APIRouter(
    prefix="/mail",
    responses={404: {"description": "not found"}}
)

class VerifyMailIn(BaseModel):
    code: int

@router.post("/verify")
async def verify_mail(vin: VerifyMailIn, user: UserInfo = Depends(dependencies.get_user_info_by_token)):
    await verify_activate_code(user.id, vin.code)

# 发送激活验证码
@router.post("/activate")
async def mail_activate(resp: Response, user: UserInfo = Depends(dependencies.get_user_info_by_token)):
    if user.activated:
        raise ServiceException(
            status.HTTP_403_FORBIDDEN,
            detail="已经验证过了!",
            code = ErrorCode.FORM.ALREADY_VERIFIED
        )
    addr = user.mail
    code = await gen_activate_code(user.id)
    await send_verify_code_mail(code, addr, "[激活]")

class GenVCodeIn(BaseModel):
    code_type: str
    mail:      str

@router.post("/gen_verify_code")
async def verify_code(*, gvci: GenVCodeIn):
    if user := await User.find_one({"mail": gvci.mail}, {"mail": 1}):
        uid = str(user['_id'])
        mail = user['mail']
        if gvci.code_type == "reset_psw":
            code = await gen_reset_psw_code(uid, 120)
            await send_verify_code_mail(code, mail, "[重置密码]")
        return
    raise ServiceException(
        status.HTTP_403_FORBIDDEN,
        detail="邮箱未注册",
        code = ErrorCode.FORM.UNKNOWN_EMAIL
    )
