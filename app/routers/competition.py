from fastapi import APIRouter, Depends, status, Cookie
from pydantic import BaseModel

from ..dependencies import get_user_permission_model, get_user_info_by_token, get_uid_from_token
from ..exceptions import ServiceException, ErrorCode
from ..database.challenge import Challenge
from ..database.competition import Competition
from ..database.event import Event
from ..DataModel import UserPermissionModel, ChallengeInfoOmitFlag

router = APIRouter(
    prefix="/competition",
    responses={404: {"description": "not found"}},
)

class ChangeChallengeForm(BaseModel):
    comp_id: str
    cha_id:  list[str]

@router.post("/append_challenges")
async def append_challenge(*, form: ChangeChallengeForm, user: UserPermissionModel = Depends(get_user_permission_model)):
    if not user.permission.Event.Write:
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权限', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await Competition.append_challenge(form.comp_id, *form.cha_id)

@router.post("/remove_challenges")
async def remove_challenges(*, form: ChangeChallengeForm, user: UserPermissionModel = Depends(get_user_permission_model)):
    if not user.permission.Event.Write:
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权限', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    await Competition.remove_challenge(form.comp_id, *form.cha_id)

@router.post("/challenges/{cid}")
async def get_challenge_list(*, cid: str, user: UserPermissionModel = Depends(get_user_permission_model)):
    # 是否存在比赛
    if comp := await Event.get(cid, user.id):
        # 是否参加/有权限
        if comp.get('joined', False) or user.permission.Challenge.Read or user.permission.Challenge.Write:
            if clist := await Competition.get_challenges_list(cid):
                res = []
                for cell in clist:
                    rec = await Challenge.get(cell.get('id'))
                    info = ChallengeInfoOmitFlag(**rec, id=str(rec['_id']), creator=str(rec['uid']))
                    res.append(info)
                return res
            else:
                return []
        else:
            raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权限', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    raise ServiceException(status.HTTP_404_NOT_FOUND, detail='不存在的比赛', code=ErrorCode.EVENT.NOT_FOUND)

@router.post("/update_challenges")
async def remove_challenges(*, form: ChangeChallengeForm, user: UserPermissionModel = Depends(get_user_permission_model)):
    if not user.permission.Event.Write:
        raise ServiceException(status.HTTP_403_FORBIDDEN, detail='无权限', code=ErrorCode.REQUEST.PERMISSION_DENIED)
    clgs = await Competition.get_challenges_list(form.comp_id)
    exist_ids = set([str(i.get('id')) for i in clgs])
    need_ids = set(form.cha_id)
    remove = exist_ids.difference(need_ids)
    append = need_ids.difference(exist_ids)
    await Competition.append_challenge(form.comp_id, *append)
    await Competition.remove_challenge(form.comp_id, *remove)

class CheckFlagIn(BaseModel):
    comp_id: str
    cha_id:  str
    flag:    str

@router.post("/check")
async def check_flag(*, cfi: CheckFlagIn, uid: str = Depends(get_uid_from_token)):
    await Competition.check_flag(uid, cfi.comp_id, cfi.cha_id, cfi.flag)

@router.post("/challenge_status/{comp_id}")
async def get_cha_status(*, comp_id: str, uid: str = Depends(get_uid_from_token)):
    clgs = await Competition.get_personal_challenges_status(uid, comp_id)
    return {v['id']: v['passed'] async for v in clgs}

@router.post("/{cid}/{id}")
async def get_challenge(*, cid: str, id: str, uid: str = Depends(get_uid_from_token)):
    rec = await Competition.get_challenge(cid, id)
    return ChallengeInfoOmitFlag(**rec, id=str(rec['_id']), creator=str(rec['uid']))
