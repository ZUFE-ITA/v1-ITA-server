from .includes import *
from .challenge import Challenge
from .event import Event
from pymongo import UpdateOne

"""db.competition
{
    _id: ObjectId
    challenges: {
        id: ObjectId,
        score: number,
        passed: {
            id: ObjectId,  # *通过的用户ID
            time: datetime
        }[]
    }[]
}
"""
class Competition:
    comp = db.competition

    @classmethod
    async def get_personal_score(cls, comp_id: str, uid: str):
        _uid = ObjectId(uid)
        _coid = ObjectId(comp_id)
        res = cls.comp.aggregate([
            {"$match": {"_id": _coid}},
            {"$unwind": "$challenges"},
            {"$unwind": "$challenges.passed"},
            {"$match": {'challenges.passed.id': _uid}},
            {
                '$group': {
                    '_id': None,
                    "score": {"$sum": "$challenges.score"}
                }
            },
        ])
        async for i in res:
            return i['score']
        
    @classmethod
    async def assert_exists(cls, comp_id: str):
        if await cls.exists(comp_id):
            return True
        raise ServiceException(
            status.HTTP_404_NOT_FOUND, detail='比赛不存在', code=ErrorCode.COMPETITION.NOT_FOUND)

    @classmethod
    async def get_score(cls, comp_id: str, cha_id: str):
        _coid = ObjectId(comp_id)
        _chid = ObjectId(cha_id)
        if rec := await cls.comp.find_one({"challenges.id": _chid}, {"challenges.$": 1}):
            return rec['challenges'][0]['score']
        raise ServiceException(
            status.HTTP_404_NOT_FOUND, detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)
        

    @classmethod
    async def get_challenge(cls, comp_id: str, cha_id: str):
        _chid = ObjectId(cha_id)
        if not await cls.comp.find_one({
            "_id": ObjectId(comp_id),
            "challenges.id": {
                '$in': [_chid]
            }
        }):
            raise ServiceException(
                status.HTTP_404_NOT_FOUND, detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)
        return await Challenge.get(_chid)

    @classmethod
    async def get_personal_challenges_status(cls, uid: str, comp_id: str):
        _uid = ObjectId(uid)
        _coid = ObjectId(comp_id)
        await cls.assert_user_in_(_uid, _coid)
        return cls.comp.aggregate([
            {"$match": {"_id": _coid}},
            {"$project": {"challenges": {"$ifNull": ["$challenges", []]}}},
            {"$unwind": "$challenges"},
            {"$unwind": "$challenges.passed"},
            {"$group": {
                "_id": {"challenge_id": "$challenges.id", "user_id": "$challenges.passed.id"},
                # "min_passed_time": {"$min": "$challenges.passed.time"},
                "passed": {"$max": {"$cond": [{"$eq": ["$challenges.passed.id", _uid]}, True, False]}}
            }},
        ])

    @classmethod
    async def assert_user_in_(cls, uid: str, comp_id: str):
        e = await Event.get(comp_id, uid)
        if e:
            if not e.get("joined", False):
                raise ServiceException(
                    status.HTTP_403_FORBIDDEN, detail='未参赛', code=ErrorCode.COMPETITION.FORBIDDEN)
        else:
            raise ServiceException(
                status.HTTP_404_NOT_FOUND, detail='比赛不存在', code=ErrorCode.COMPETITION.NOT_FOUND)

    @classmethod
    async def if_stop(cls, comp_id: str):
        return await Event.if_stop(comp_id)

    @classmethod
    async def check_flag(cls, uid: str, comp_id: str, cha_id: str, flag: str):
        _coid = ObjectId(comp_id)
        _chid = ObjectId(cha_id)
        _uid = ObjectId(uid)
        await cls.assert_user_in_(uid, _coid)
        # 检查有没有提交过
        rec = cls.comp.aggregate([
            {"$match": {"_id": _coid}},
            {"$unwind": "$challenges"},
            {"$match": {"challenges.id": _chid}},
            {"$unwind": '$challenges.passed'},
            {"$match": {"challenges.passed.id": _uid}}
        ])
        async for _ in rec:
            raise ServiceException(
                status.HTTP_418_IM_A_TEAPOT, detail='提交过了', code=ErrorCode.COMPETITION.ALREADY_PASSED)

        # passed = await cls.get_passed_list(_coid, _chid)
        # if _uid in passed:
        #     raise ServiceException(
        #         status.HTTP_418_IM_A_TEAPOT, detail='提交过了', code=ErrorCode.COMPETITION.ALREADY_PASSED)
        # 检查flag
        await Challenge.check_flag(_chid, flag)
        update = await cls.comp.update_one({
            "_id": _coid,
            "challenges": {'$elemMatch': {"id": _chid}}
        }, {
            "$push": {
                'challenges.$.passed': {
                    'id': _uid,
                    'time': datetime.now()
                }
            }
        })
        if update.matched_count:
            return True
        raise ServiceException(status.HTTP_404_NOT_FOUND,
                               detail='题目不存在', code=ErrorCode.CHALLENGE.NOT_FOUND)

    @classmethod
    async def exists(cls, id: ObjectId | str):
        rec = await cls.comp.find_one({"_id": ObjectId(id)}, {"_id": 1})
        return rec is not None
    
    @classmethod
    async def bulk_write(cls, op):
        return await cls.comp.bulk_write(op)

    @classmethod
    async def bulk_write_append_challenge(cls, comp_id: str, *scores: Score, upsert=True):
        _cid = ObjectId(comp_id)
        push = [{
            'id': ObjectId(i.id),
            "score": i.score,
            "passed": []
        } for i in scores]
        return UpdateOne({"_id": _cid}, {
            "$push": {
                'challenges': {"$each": push}
            }
        }, upsert=upsert)

    @classmethod
    async def bulk_write_remove_challenge(cls, comp_id: str, *cha_id: str):
        _coid = ObjectId(comp_id)
        _chid = [ObjectId(i) for i in set(cha_id)]
        if not await cls.exists(_coid):
            raise ServiceException(
                status.HTTP_404_NOT_FOUND, detail='比赛不存在', code=ErrorCode.COMPETITION.NOT_FOUND)
        return UpdateOne({"_id": _coid, }, {
            "$pull": {
                'challenges': {
                    "id": {"$in": _chid}
                }
            }
        })
    
    @classmethod
    async def bulk_write_update_score(cls, scores: ChangeChallengeForm):
        _coid = ObjectId(scores.comp_id)
        return [UpdateOne(
        {
            '_id': _coid,
            'challenges.id': ObjectId(s.id)
        },
        {
            '$set': {'challenges.$.score': s.score}
        }) for s in scores.scores]

    @classmethod
    async def get_challenges_list(cls, comp_id: str):
        _id = ObjectId(comp_id)
        resp = await cls.comp.find_one({"_id": _id}, {"challenges": 1})
        if resp:
            return resp.get("challenges", [])
        else:
            return []

    @classmethod
    async def get_rank(cls, comp_id: str):
        _coid = ObjectId(comp_id)
        await cls.assert_exists(_coid)
        return cls.comp.aggregate([
            {"$match": {"_id": _coid}},
            {"$unwind": "$challenges"},
            {"$unwind": "$challenges.passed"},
            {
                "$group": {
                    '_id': "$challenges.passed.id",
                    'count': {"$sum": 1},
                    "score": {"$sum": "$challenges.score"},
                    'avg_time': { '$avg': {'$toLong': "$challenges.passed.time" } },
                }
            }
        ])
    