from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from ..dependencies import UserInfo, UserInfoWithPermission
from .. import dependencies
from ..database import  User, verify_reset_psw_code
from ..utils.token_utils import generate_user_token, set_cookie
from ..utils import check_psw
from ..exceptions import ServiceException, ErrorCode

router = APIRouter(
    prefix="/user",
    responses={404: {"description": "not found"}}
)

class InfoIn(BaseModel):
    id: str

class InfoOut(BaseModel):
    id: str
    username: str
    signature: str = ''

@router.post("/info")
async def user_info(info_in: InfoIn):
    info = await User.find_by_id(info_in.id, {'signature': 1, "username": 1})
    return InfoOut(id=info_in.id, **info)

class LoginIn(BaseModel):
    mail: str
    psw: str
    remember: bool

@router.post("/login")
async def login(
    *,
    user: UserInfoWithPermission = Depends(dependencies.login),
    form: LoginIn,
    response: Response
):
    id = user.id
    age = 31536000 if form.remember else None
    access_token = await generate_user_token(id, age)
    set_cookie(response, "token", access_token, max_age=age)
    return user

@router.post("/auth")
async def auth(user: UserInfoWithPermission = Depends(dependencies.get_user_info_by_token)):
    return user

@router.post("/register")
async def register(resp: Response, register_result: UserInfoWithPermission = Depends(dependencies.register)):
    access_token = await generate_user_token(register_result.id, 1800)
    set_cookie(resp, "token", access_token, max_age=1800)
    return register_result

@router.post("/logout")
async def logout(response: Response):
    set_cookie(response, "token", "", max_age=0)

class ResetPswIn(BaseModel):
    mail: str
    psw:  str
    code: str

@router.post("/reset_psw")
async def reset_psw(*, rin: ResetPswIn):
    if user := await User.find_one({"mail": rin.mail}):
        if check_psw(rin.psw):
            await verify_reset_psw_code(str(user['_id']), rin.code, rin.psw)
            return True
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST,
            detail="密码太简单",
            code = ErrorCode.FORM.PSW_TOO_SIMPLE
        )
    raise ServiceException(
        status.HTTP_403_FORBIDDEN,
        detail="不存在的邮箱",
        code = ErrorCode.FORM.UNKNOWN_EMAIL
    )

class UserEvent(BaseModel):
    id:      str
    type:    str
    title:   str|None  = None
    caption: str|None  = None

class UserEventOut(BaseModel):
    username: str
    uid:      str
    events:   list[UserEvent]

class UpdateSignIn(BaseModel):
    sign: str

@router.post("/update/sign")
async def updateSign(*, user: UserInfo = Depends(dependencies.get_user_info_by_token), si: UpdateSignIn):
    if len(si.sign) > 50:
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST, 
            detail = "太长了签名", 
            code=ErrorCode.FORM.SIGNATURE_TOO_LONG
        )
    await User.update_signature(user.id, si.sign)

class UpdateUsernameIn(BaseModel):
    username: str

@router.post("/update/username")
async def updateSign(*, user: UserInfo = Depends(dependencies.get_user_info_by_token), uui: UpdateUsernameIn):
    if len(uui.username) > 20:
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST, 
            detail = "太长了名字", 
            code=ErrorCode.FORM.USERNAME_TOO_LONG
        )
    await User.update_username(user.id, uui.username)

class CommonUserInfo(BaseModel):
    id:         str
    username:   str
    signature:  str|None = None

@router.get("/{uid}")
async def get_iser_info(uid: str):
    info = await User.find_by_id(uid)
    return CommonUserInfo(**info, id=str(info['_id']))