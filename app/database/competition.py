from .includes import *
from .challenge import Challenge
from .event import Event

"""db.competition
{
    _id: ObjectId
    challenges: [
        {
            id: ObjectId,
            passed: list[ObjectId] # *通过的用户ID
        }
    ]
}
"""
"""db.competition_passed_challenge
{
    _id: ObjectId,
    uid: ObjectId,
    comp_id: ObjectId,
    passed: list[ObjectId] # *通过的题目ID
}
"""
class Competition:
    comp = db.competition
    passed = db.competition_passed_challenge

    @classmethod
    async def get_challenge(cls, comp_id: str, cha_id: str):
        _chid = ObjectId(cha_id)
        if not await cls.comp.find_one({
            "_id": ObjectId(comp_id), 
            "challenges.id": {
                '$in': [_chid]
            }
        }):
            raise ServiceException(status.HTTP_404_NOT_FOUND, detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)
        return await Challenge.get(_chid)
    
    @classmethod
    async def get_personal_challenges_status(cls, uid: str, comp_id: str):
        _uid = ObjectId(uid)
        _coid = ObjectId(comp_id)
        await cls.assert_user_in_(_uid, _coid)
        return cls.comp.aggregate([
            {"$limit": 1},
            {"$match": {"_id": _coid}},
            {"$project": {"challenge": {"$ifNull": ["$challenges", []]}}},
            {"$unwind": '$challenge'},
            {
                "$project": {
                    "id": {"$toString": '$challenge.id'},
                    "passed": {"$in": [_uid, "$challenge.passed"]}
                }
            }
        ])

    @classmethod
    async def get_passed_list(cls, comp_id: str, cha_id: str):
        """ 得到题目的通过者列表"""
        _coid = ObjectId(comp_id)
        _chid = ObjectId(cha_id)
        async for passed in cls.comp.aggregate([
            {"$limit": 1},
            {"$match": {"_id": _coid}},
            {"$unwind": "$challenges",},
            {
                "$project": {
                    "id": "$challenges.id",
                    "passed": {"$ifNull": ["$challenges.passed", []]}
                }
            },
            {"$match": {"id": _chid}}
        ]):
            passed = passed.get("passed", []) # type: list[ObjectId]
            return passed
        raise ServiceException(status.HTTP_404_NOT_FOUND, detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)

    @classmethod
    async def assert_user_in_(cls, uid: str, comp_id: str):
        e = await Event.get(comp_id, uid)
        if e:
            if not e.get("joined", False):
                raise ServiceException(status.HTTP_403_FORBIDDEN, detail='未参赛', code=ErrorCode.COMPETITION.FORBIDDEN)
        else:
            raise ServiceException(status.HTTP_404_NOT_FOUND, detail='比赛不存在', code=ErrorCode.COMPETITION.NOT_FOUND)
    

    @classmethod
    async def check_flag(cls, uid: str, comp_id: str, cha_id: str, flag: str):
        _coid = ObjectId(comp_id)
        _chid = ObjectId(cha_id)
        _uid = ObjectId(uid)
        await cls.assert_user_in_(uid, _coid)
        passed = await cls.get_passed_list(_coid, _chid)
        if _uid in passed:
            raise ServiceException(status.HTTP_418_IM_A_TEAPOT, detail='提交过了', code=ErrorCode.COMPETITION.ALREADY_PASSED)
        # 检查flag
        await Challenge.check_flag(_chid, flag)
        update = await cls.comp.update_one({
            "_id": _coid,
            "challenges": { '$elemMatch': { "id": _chid } }
        }, {
            "$push": {
                'challenges.$.passed': _uid
            }
        })
        if update.matched_count:
            return True
        raise ServiceException(status.HTTP_404_NOT_FOUND, detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)


    @classmethod
    async def exists(cls, id: ObjectId|str):
        rec = await cls.comp.find_one({"_id": ObjectId(id)}, {"_id": 1})
        return rec is not None

    @classmethod
    async def append_challenge(cls, comp_id: str, *cha_id: str):
        if len(cha_id) == 0:
            return 0
        _cid = ObjectId(comp_id)
        push = [{
            'id': ObjectId(i),
            "passed": []
        } for i in set(cha_id)]
        if await cls.exists(_cid):
            res = await cls.comp.update_one({"_id": _cid}, {
                "$push": {
                    'challenges': {"$each": push}
                }
            })
        else:
            res = await cls.comp.insert_one({"_id": _cid, "challenges": push})
        return res

    @classmethod
    async def remove_challenge(cls, comp_id: str, *cha_id: str):
        if len(cha_id) == 0:
            return 0
        _coid = ObjectId(comp_id)
        _chid = [ ObjectId(i) for i in set(cha_id)]
        if not await cls.exists(_coid):
            raise ServiceException(status.HTTP_404_NOT_FOUND, detail='比赛不存在', code=ErrorCode.COMPETITION.NOT_FOUND)
        update = await cls.comp.update_one({ "_id": _coid, }, {
            "$pull": {
                'challenges': {
                    "id": {"$in": _chid}
                }
            }
        })
        return update.modified_count

    @classmethod
    async def get_challenges_list(cls, comp_id: str):
        _id = ObjectId(comp_id)
        resp = await cls.comp.find_one({"_id": _id}, {"challenges": 1})
        if resp:
            return resp.get("challenges", [])
        else:
            return []
