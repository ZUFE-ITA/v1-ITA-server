from fastapi import APIRouter, Depends, status, Cookie
from pydantic import BaseModel

from ..dependencies import get_user_permission_model, get_user_info_by_token
from ..exceptions import ServiceException, ErrorCode
from ..database.challenge import Challenge
from ..DataModel import UserPermissionModel, UserInfo, ChallengeInfo, ChallengeCreateForm
from ..utils.token_utils import get_id_from_token

router = APIRouter(
    prefix="/challenge",
    responses={404: {"description": "not found"}},
)

class ChallengeCreateResult(BaseModel):
    id: str

@router.post("/create")
async def challenge_create(*, user:UserPermissionModel = Depends(get_user_permission_model), form: ChallengeCreateForm):
    if user.permission.Challenge.Write:
        res = await Challenge.create(user.id, form)
        return ChallengeCreateResult(id=str(res.inserted_id))
    raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)

@router.post("/list/{label}")
async def challenge_list(*, user: UserPermissionModel = Depends(get_user_permission_model), label: str):
    if user.permission.Challenge.Read:
        return [
            ChallengeInfo(**cell, id=str(cell['_id']), creator=str(cell['uid'])) 
            for cell in await Challenge.list(label)
        ]
    raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)

@router.post("/update/{id}")
async def update_challenge(*, id: str, user: UserPermissionModel=Depends(get_user_permission_model), form: ChallengeCreateForm):
    if not user.permission.Challenge.Write:
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权操作', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await Challenge.update(id, form)

@router.post("/{id}")
async def get_challenge_info(*, id: str, user: UserPermissionModel = Depends(get_user_permission_model)):
    if user.permission.Challenge.Read:
        rec = await Challenge.get(id)
        return ChallengeInfo(**rec, id=str(rec['_id']), creator=str(rec['uid']))
