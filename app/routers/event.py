from fastapi import APIRouter, Depends, Response, status, Cookie
from pydantic import BaseModel

from ..dependencies import get_user_permission_model, get_user_info_by_token
from ..exceptions import ServiceException, ErrorCode
from ..database.event import Event as evt
from ..DataModel import UserPermissionModel, EventCreateForm, EventCreateResult, EventInfo, JoinInModel, UserInfo
from ..utils.permission import Event
from ..utils.token import get_id_from_token

router = APIRouter(
    prefix="/event",
    responses={404: {"description": "not found"}}
)

@router.post("/create")
async def event_create(*, user:UserPermissionModel = Depends(get_user_permission_model), form: EventCreateForm):
    if user.permission.can(Event.Append):
        create_res = await evt.create(user.id, form)
        return EventCreateResult(id=str(create_res.inserted_id))
    raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)

@router.post("/list")
async def event_list(token: str | None = Cookie(default=None)):
    if token:
        uid = get_id_from_token(token)
        return [EventInfo(**cell, id=str(cell['_id']), creator=str(cell['uid'])) for cell in await evt.list(uid)]
    return [EventInfo(**cell, id=str(cell['_id']), creator=str(cell['uid'])) for cell in await evt.list()]

@router.post("/join")
async def join_event(*, jin: JoinInModel, user: UserPermissionModel = Depends(get_user_permission_model)):
    if user.permission.cannot(Event.Join):
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await evt.join(user.id, jin.id)

@router.post("/exit")
async def join_event(*, jin: JoinInModel, user: UserPermissionModel = Depends(get_user_permission_model)):
    if user.permission.cannot(Event.Join):
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await evt.exit(user.id, jin.id)

@router.post("/joined")
async def get_joined_events(user: UserInfo = Depends(get_user_info_by_token)):
    li = await evt.get_joined_list(user.id, str)
    return li

@router.post("/update/{id}")
async def update_event(*, id: str, user: UserPermissionModel=Depends(get_user_permission_model), form: EventCreateForm):
    if user.permission.cannot(Event.Append):
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await evt.update(id, form)

@router.post("/{id}")
async def get_event_info(*, id: str, token: str | None = Cookie(default=None)):
    if token:
        uid = get_id_from_token(token)
    else:
        uid = None
    e = await evt.get(id, uid)
    return EventInfo(**e, id=str(e['_id']), creator=str(e['uid']))