from .includes import *

class Article:
    col = db.bbs

    @classmethod
    async def delete(cls, id: str):
        _id = ObjectId(id)
        return cls.col.delete_one({'_id': _id})

    @classmethod
    async def get_author_id_by_id(cls, id: str):
        _id = ObjectId(id)
        return cls.col.find_one({"_id": _id}, {'uid': 1})

    @classmethod
    async def get_summary_by_uid(cls, uid: str, summary_size=100):
        _uid = ObjectId(uid)
        return cls.col.aggregate([
            {"$match": {"uid": _uid }},
            {'$sort': { "_id": -1 }},
            {
                "$project": {
                    "_id": 1,
                    "sub": 1,
                    "summary": {
                        "$substrCP": ["$content", 0, summary_size]
                    },
                    "tags": 1,
                    'update': 1,
                },
            }
        ])

    @classmethod
    async def estimated_document_count(cls):
        return cls.col.estimated_document_count()
    
    @classmethod
    async def get_summary_by_range(cls, start: int, size: int, summary_size=100):
        return cls.col.aggregate([
            {'$sort': { "_id": -1 }},
            {"$skip": start},
            {"$limit": size},
            {
                "$project": {
                    "_id": 1,
                    'uid': 1,
                    "sub": 1,
                    "summary": {
                        "$substrCP": ["$content", 0, summary_size]
                    },
                    "tags": 1,
                    'update': 1,
                },
            }
        ])

    @classmethod
    async def exists(cls, *, id: str = None, _id: ObjectId = None):
        assert id is not None or _id is not None
        return cls.col.find_one({"_id": _id if _id is not None else ObjectId(id)}, {"_id": 1})

    @classmethod
    async def comment(cls, uid: str, text: str, pid: str):
        return await Comment.comment(uid, text, pid)

    @classmethod
    async def push(cls, uid: str, doc: DocIn):
        data = {
            "uid": ObjectId(uid),
            "sub"   : doc.sub,
            "content"  : doc.content,
        }
        return cls.col.insert_one(data)

    @classmethod
    async def get_by_id(cls, pid: str):
        _pid = ObjectId(pid)
        return cls.col.find_one({"_id": _pid})

    @classmethod
    async def summaries(cls, limit: int, prev_id: str = None, summary_size=100):
        pipeline = [] if prev_id is None else [{
            "$match": {
                '_id': {
                    "$lt": ObjectId(prev_id)
                }
            }
        }]
        pipeline.extend([
            {
                "$project": {
                    "_id": 1,
                    'uid': 1,
                    "sub": 1,
                    "summary": {
                        # content取前summary_size个字
                        "$substrCP": ["$content", 0, summary_size]
                    },
                    "tags": 1,
                    'update': 1,
                },
            },
            {
                '$sort': {
                    "_id": -1
                }
            },
            {
                "$limit": limit
            }
        ])
        cur = cls.col.aggregate(pipeline)
        return cur

class Comment:

    col = db.article_comment

    @classmethod
    async def get_author_id_by_id(cls, id: str):
        _id = ObjectId(id)
        return cls.col.find_one({"_id":_id}, {"uid": 1})
    
    @classmethod
    async def delete(cls, id: str):
        _id = ObjectId(id)
        _sup = cls.col.find_one({"_id": _id}, {'sup': 1}).get("sup", None)
        if _sup is  not None:
            cls.col.update_one({"_id": _sup}, { "$pull": { "sub": _id } })
        return cls.col.delete_one({"_id": _id})

    @classmethod
    async def estimated_document_count(cls):
        return cls.col.estimated_document_count()

    @classmethod
    async def exists(cls, *, id: str = None, _id: ObjectId = None):
        assert id is not None or _id is not None
        return cls.col.find_one({"_id": _id if _id is not None else ObjectId(id)}, {"like":0, "sub": 0})
    
    @classmethod
    async def get(cls, cid: str, uid: str = None):
        _cid = ObjectId(cid)
        if uid is None:
            cur = cls.col.aggregate([
                {"$match": { "_id": {"$eq": _cid}}},
                {'$project': {
                    "_id": 1,
                    "uid": 1,
                    "text": 1,
                    "n_like": { "$cond": {
                        "if": { "$isArray": "$like" },
                        "then": { "$size": "$like" },
                        "else": 0
                    } },
                    "n_comment": { "$cond": {
                        "if": { "$isArray": "$sub" },
                        "then": { "$size": "$sub" },
                        "else": 0
                    } },
                }}
            ])
        else:
            cur = cls.col.aggregate([
                {"$match": { "_id": {"$eq": _cid}}},
                {'$project': {
                    "_id": 1,
                    "uid": 1,
                    "text": 1,
                    "n_like": { "$cond": {
                        "if": { "$isArray": "$like" },
                        "then": { "$size": "$like" },
                        "else": 0
                    } },
                    "n_comment": { "$cond": {
                        "if": { "$isArray": "$sub" },
                        "then": { "$size": "$sub" },
                        "else": 0
                    } },
                    "liked": { "$cond": {
                        "if": {"$isArray": "$like"},
                        "then": {"$in": [ObjectId(uid), "$like"]},
                        "else": False
                    } }
                }}
            ])
        for d in cur:
            return d
        raise ServiceException(
            status.HTTP_404_NOT_FOUND,
            detail = "不存在的评论",
            code = ErrorCode.BBS.UNKNOWN_COMMENT
        )
    
    @classmethod
    async def comment(cls, uid: str, text: str, pid: str=None, cid:str = None):
        """cid = None表示回复的是帖子而不是评论"""
        if cid is None:
            # 检查帖子存不存在
            if pid is None:
                raise ServiceException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail='pid is None',
                    code = ErrorCode.BBS.UNKNOWN_ARTICLE
                )
            _pid = ObjectId(pid)
            if await Article.exists(_id = _pid):
                return cls.col.insert_one({
                    "pid": _pid,
                    "uid": ObjectId(uid),
                    "text": text,
                })
            raise ServiceException(
                status.HTTP_400_BAD_REQUEST, 
                detail="帖子不存在",
                code = ErrorCode.BBS.UNKNOWN_ARTICLE
            )
        # 检查评论存不存在
        _cid = ObjectId(cid)
        if doc := await Comment.exists(_id=_cid):
            _pid = doc['pid']
            if pid is not None and ObjectId(pid) != _pid:
                raise ServiceException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail='different pid',
                    code = ErrorCode.BBS.UNKNOWN_ARTICLE
                )
            rec = cls.col.insert_one({
                    "pid": _pid,
                    "uid": ObjectId(uid),
                    "text": text,
                    'sup': _cid
            })
            cls.col.update_one({"_id": _cid}, {"$push": {"sub": rec.inserted_id}})
            return rec
        raise ServiceException(
            status.HTTP_400_BAD_REQUEST,
            detail="评论不存在",
            code = ErrorCode.BBS.UNKNOWN_COMMENT
        )

    @classmethod
    async def like(cls, uid: str, cid: str):
        return cls.col.update_one({"_id": ObjectId(cid)}, {
            "$addToSet": {"like": ObjectId(uid)}
        })
    
    @classmethod
    async def dislike(cls, uid: str, cid: str):
        return cls.col.update_one({"_id": ObjectId(cid)}, {
            "$pull": {"like": ObjectId(uid)}
        })
    
    @classmethod
    async def list_of_article(cls, pid: str, prev_cid: str = None, limit=20, uid:str = None):
        """uid 用于判断是否点过赞了"""
        # TODO: 按需加载
        proj = {
            "_id": 1,
            "uid": 1,
            "text": 1,
            "n_like": { "$cond": {
                "if": { "$isArray": "$like" },
                "then": { "$size": "$like" },
                "else": 0
            } },
            "n_comment": { "$cond": {
                "if": { "$isArray": "$sub" },
                "then": { "$size": "$sub" },
                "else": 0
            } },
        }
        match_cond = { 
            "pid": {"$eq": ObjectId(pid)},
            "$or": [
                {"sup": {"$exists": False}},
                {"sup": {"$eq": None}}
            ]
        } 
        if uid is None:
            pipeline = [
                { "$match": match_cond },
                { "$project": proj },
                { "$sort": {"_id": 1} },
            ]
        else:
            pipeline = [
                { "$match": match_cond },
                {
                    "$project": {
                        **proj,
                        "liked": { "$cond": {
                            "if": {"$isArray": "$like"},
                            "then": {"$in": [ObjectId(uid), "$like"]},
                            "else": False
                        } }
                    }
                },
                { "$sort": {"_id": 1} },
            ]
        return cls.col.aggregate(pipeline)

    @classmethod
    async def list_of_comment(cls, cid: str, prev_cid: str = None, limit=20, uid:str = None):
        tmp = {
            "_id": 1,
            "uid": 1,
            "text": 1,
            "n_like": { "$cond": {
                "if": { "$isArray": "$like" },
                "then": { "$size": "$like" },
                "else": 0
            } },
            "n_comment": { "$cond": {
                "if": { "$isArray": "$sub" },
                "then": { "$size": "$sub" },
                "else": 0
            } },
        }
        match_cond = { "sup": {"$eq": ObjectId(cid)} } 
        if uid is None:
            pipeline = [
                { "$match": match_cond },
                { "$project": tmp },
                { "$sort": {"_id": 1} },
            ]
        else:
            pipeline = [
                { "$match": match_cond },
                {
                    "$project": {
                        **tmp,
                        "liked": { "$cond": {
                            "if": {"$isArray": "$like"},
                            "then": {"$in": [ObjectId(uid), "$like"]},
                            "else": False
                        } }
                    }
                },
                { "$sort": {"_id": 1} },
            ]
        return cls.col.aggregate(pipeline)