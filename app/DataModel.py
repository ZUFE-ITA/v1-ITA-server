import re
from pydantic import BaseModel, validator
from datetime import datetime
from fastapi import status
from .exceptions import ServiceException, ErrorCode
from .utils import checker
from .utils.permission import PermissionModel
class UsernameModel(BaseModel):

    username: str

    @validator('username')
    def name_check(cls, v: str):
        if not checker.check_username(v):
            raise ServiceException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid username",
                code = ErrorCode.FORM.INVALID_USERNAME
            )
        return v.strip()

class StuNoModel(BaseModel):

    no: str

    @validator('no')
    def name_check(cls, v: str):
        v = v.strip()
        if re.match("^[0-9]+$", v):
            return v.strip()
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST,
            detail = '学号错误',
            code=ErrorCode.FORM.NO_FORMAT_ERROR
        )

class RegisterForm(UsernameModel, StuNoModel):
    mail: str
    psw:  str

    @validator("psw")
    def p1_check(cls, v: str):
        if not checker.check_psw(v):
            raise ServiceException(
                status.HTTP_400_BAD_REQUEST,
                detail="invalid password", 
                code=ErrorCode.FORM.INVALID_PSW
            )
        return v

class RegisterRecord(UsernameModel, StuNoModel):
    mail:      str
    activated:  bool = False  # 邮箱认证标识
    psw:        bytes
    permission: str

class RegisterResult(BaseModel):
    id:     str
    record: RegisterRecord

class LoginForm(BaseModel):
    mail:    str
    psw:      str

class Currency(BaseModel):
    soap: int|None  = None
    pants: int|None = None

class UserInfo(BaseModel):
    id:             str
    mail:           str
    username:       str
    activated:      bool          = False
    signature:      str|None      = None
    currency:       Currency|None = None

class Token(BaseModel):
    access_token:  str
    token_type:    str

class TokenData(BaseModel):
    sub: str

class Author(BaseModel):
    id:   str
    username: str

# 一般返回给前端
class DocModel(BaseModel):
    id:          str
    tags:        list[str] | None = None
    sub:         str
    content:     str
    update:      datetime  | None = None
    author:      Author

class SummaryModel(BaseModel):
    id:          str
    tags:        list[str] | None = None
    sub:         str
    summary:     str
    update:      datetime  | None = None
    author:      Author

class DocRecord(BaseModel):
    tags:        list[str]
    doc:         str
    create_time: datetime
    update_time: datetime
    author:      Author

class DocIn(BaseModel):
    sub: str
    content: str

class TimeRangeModel(BaseModel):
    start: datetime
    end: datetime

class DeleteIn(BaseModel):
    id: str


# 权限模型
class GroupUserInfo(BaseModel):
    user:  UserInfo
    group: str

class Permission(BaseModel):
    origin: str

class UserInfoWithPermission(UserInfo):
    permission: str

class UserPermissionModel(BaseModel):
    id: str
    permission: PermissionModel
    class Config:
        arbitrary_types_allowed = ['permission']

# 事件
class EventCreateForm(BaseModel):
    title:         str
    desc:          str
    organizer:     str
    addr:          str
    longtime:      bool
    range:         TimeRangeModel | None = None
    start:         datetime | None = None
    with_point:    bool
    point_detail:  str | None = None
    with_reward:   bool
    reward_detail: str | None = None
    limit_count:   bool
    max_count:     int | None = None
    need_check:    bool
    deadline: datetime

class EventCreateResult(BaseModel):
    id: str

class EventInfo(EventCreateForm):
    id:     str
    creator:str 
    joined: bool = False

class JoinInModel(BaseModel):
    id: str