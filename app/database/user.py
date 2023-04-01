import time
import random

from .includes import *

class User:

    user_col = db.user_info
    check_in_col = db.check_in

    @classmethod
    async def count_checked_in(cls, uid: str):
        _uid = ObjectId(uid)
        return await cls.check_in_col.count_documents({"uid": _uid})

    @classmethod
    async def last_time_checked_in(cls, uid: str | ObjectId):
        _uid = ObjectId(uid)
        for rec in await cls.check_in_col.find({"uid": _uid}).sort("_id", -1).limit(1):
            _id = str(rec.get("_id"))[:8]
            return int(_id, 16)
        return 0

    @classmethod
    async def find(cls, condition = {}, limit=0, *args, **kwargs):
        return await cls.user_col.find(condition, *args, **kwargs).limit(limit)

    @classmethod
    async def find_one(cls, condition = {}, *args, **kwargs):
        return await cls.user_col.find_one(condition, *args, **kwargs)

    @classmethod
    async def find_by_id(cls, id: str, *args):
        _id = ObjectId(id)
        return await cls.user_col.find_one({"_id": _id}, *args)

    @classmethod
    async def insert_one(cls, user):
        insert = await cls.user_col.insert_one(user)
        return insert

    @classmethod
    async def update_info(cls, uid: str, info: dict):
        _uid = ObjectId(uid)
        up = await cls.user_col.update_one({"_id": _uid}, {
            "$set": info
        })
        if up.matched_count == 0:
            raise ServiceException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="unknown user",
                code = ErrorCode.FORM.UNKNOWN_ACCOUNT
            )
    
    @classmethod
    async def update_signature(cls, uid: str, sign: str):
        return await cls.update_info(uid, {
            "signature": sign
        })
    
    @classmethod
    async def exists(cls, **kwargs):
        return await cls.user_col.find_one(kwargs, {'_id':1})

    @classmethod
    async def update_username(cls, uid: str, username: str):
        if await User.exists(username = username):
            raise ServiceException(
                status.HTTP_400_BAD_REQUEST,
                detail = "名字重复了",
                code = ErrorCode.FORM.USERNAME_CONFLICT
            )
        return await cls.update_info(uid, {
            "username": username
        })


    @classmethod
    async def get_username_by_uid(cls, uid: str):
        username = r.get_username(uid)
        if username is None:
            info = await cls.find_by_id(uid, {"username": 1})
            username = info['username']
            r.set_username(uid, username)
        return username

    @classmethod
    async def check_in(cls, uid: str):
        _uid = ObjectId(uid)
        now_time = time.time()
        date_time = (now_time - (now_time- time.timezone) % 86400)
        last = await User.last_time_checked_in(_uid)

        if last < date_time:
            soap = random.random() * 50

            sess = client.start_session(causal_consistency=True)
            sess.start_transaction()

            try:
                await cls.check_in_col.insert_one({
                    'uid': _uid,
                    "reward": {
                        "soap": soap
                    }
                })
                await Currency.inc(uid, soap=soap)
            except Exception as e:
                sess.abort_transaction()
                sess.end_session()
                raise e
            else:
                sess.commit_transaction()
                sess.end_session()
            return {"soap": soap}

        raise ServiceException(
            status.HTTP_400_BAD_REQUEST,
            detail="签过了",
            code = ErrorCode.BBS.ALREADY_CHECKED_IN
        )
