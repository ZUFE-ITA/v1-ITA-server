from .includes import *

class Challenge:
    
    col = db.challenge

    @classmethod
    async def get(cls, id: str):
        _id = ObjectId(id)
        return cls.col.find_one({"_id": _id})

    @classmethod
    async def list(cls, label: str):
        return cls.col.find({'label': label})
    
    @classmethod
    async def create(cls, uid: str, form: ChallengeCreateForm):
        _uid = ObjectId(uid)
        return cls.col.insert_one({"uid": _uid, **form.dict(exclude_none=True)})

    @classmethod
    async def update(cls, id: str, form: ChallengeCreateForm):
        cls.col.update_one({"_id": ObjectId(id)}, {"$set": form.dict(exclude_none=True)})
