from .includes import *

class Challenge:
    
    col = db.challenge

    @classmethod
    async def get(cls, id: str|ObjectId):
        _id = ObjectId(id)
        return await cls.col.find_one({"_id": _id})

    @classmethod
    async def list(cls, label: str = None):
        if label is None:
            return cls.col.find({})
        return cls.col.find({'label': label})
    
    @classmethod
    async def create(cls, uid: str, form: ChallengeCreateForm):
        _uid = ObjectId(uid)
        return await cls.col.insert_one({"uid": _uid, **form.dict(exclude_none=True)})

    @classmethod
    async def update(cls, id: str, form: ChallengeCreateForm):
        await cls.col.update_one({"_id": ObjectId(id)}, {"$set": form.dict(exclude_none=True)})

    @classmethod
    async def check_flag(cls, id: str, flag: str):
        _id = ObjectId(id)
        if rec := await cls.col.find_one({"_id": _id}, {'flag': 1}):
            if rec.get("flag", '') == flag:
                return True
            raise ServiceException(status.HTTP_406_NOT_ACCEPTABLE, detail='wrong flag', code=ErrorCode.CHALLENGE.FLAG_WRONG)
        raise ServiceException(status.HTTP_404_NOT_FOUND, detail='cha not found', code=ErrorCode.CHALLENGE.NOT_FOUND)
