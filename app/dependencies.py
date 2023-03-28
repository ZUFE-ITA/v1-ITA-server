from fastapi import Cookie, status, HTTPException, Depends
import re
import bcrypt
from jose import JWTError

from . import database as db
from .exceptions import ServiceException, ErrorCode
from .DataModel import *
from .utils.token import get_id_from_token
from .utils.permission import DEFAULT_PERMISSION
from .utils.helper import hash_psw

def isEmail(email: str):
    return email and re.match("^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", email)


def isTel(tel: str):
    return tel and re.match(r"^[0-9]{11}$", tel)

def checkRegisterForm(form: RegisterForm):
    if not isEmail(form.mail):
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST,
            detail="invalid email",
            code = ErrorCode.FORM.INVALID_EMAIL
        )

""" ==== 注册相关依赖 ==== """
# 通过表单生成用户记录(数据库格式)
def generateUser(form: RegisterForm):
    psw = hash_psw(form.psw)
    d = form.dict()
    d['psw'] = psw
    record = RegisterRecord(**d, permission=DEFAULT_PERMISSION)
    return record


async def register(form: RegisterForm):
    """注册一个新用户"""
    checkRegisterForm(form)
    # 唯一性检测
    if await db.User.find_one({"username": form.username}):
        raise ServiceException(
            status_code=400,
            detail="用户名被注册过啦~",
            code = ErrorCode.FORM.USERNAME_CONFLICT
        )
    if await db.User.find_one({"mail": form.mail}):
        raise ServiceException(
            status_code=400,
            detail="邮箱被注册过啦~",
            code = ErrorCode.FORM.EMAIL_CONFLICT
        )
    user_info = generateUser(form)
    insert_res = await db.User.insert_one(user_info.dict())
    return UserInfoWithPermission(**user_info.dict(), id=str(insert_res.inserted_id))


""" ==== Login Dependencies ==== """


async def login(form: LoginForm):
    # 只允许邮箱登录
    if not isEmail(form.mail):
        raise ServiceException(
            status_code=400,
            detail="invalid email",
            code = ErrorCode.FORM.INVALID_EMAIL
        )

    record = await db.User.find_one({"mail": form.mail})
    if not record:
        raise ServiceException(
            status_code=400,
            detail="邮箱未注册",
            code = ErrorCode.FORM.UNKNOWN_EMAIL
        )

    hashed = record['psw']

    if bcrypt.checkpw(form.psw.encode('utf8'), hashed):
        return UserInfoWithPermission(**record, id=str(record['_id']))

    raise ServiceException(
        status_code=400,
        detail="密码错误",
        code = ErrorCode.FORM.PSW_WRONG
    )


""" ==== Token Dependencies ==== """

async def get_user_info_by_token(token: str | None = Cookie(default=None)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        id = get_id_from_token(token)
        if id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_info_by_id(id)
    if not user:
        raise ServiceException(400, detail="unknown account", code = ErrorCode.FORM.UNKNOWN_ACCOUNT)
    return user


async def get_user_info_by_id(id: str):
    if id:
        info = await db.User.find_by_id(id)
        if info:
            return UserInfoWithPermission(**info, id=str(info['_id']))
    return None

async def get_user_permission_model(user: UserInfoWithPermission = Depends(get_user_info_by_token)):
    pm = PermissionModel(user.permission)
    return UserPermissionModel(id=user.id, permission=pm)

""" ==== File ==== """

async def get_file(hash: str):
    gout = await db.File.load(hash)
    if gout:
        return gout
    raise ServiceException(status.HTTP_404_NOT_FOUND, detail='file not found')
