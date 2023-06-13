#!/usr/bin/env python
from pymongo import MongoClient
from argparse import ArgumentParser
from pydantic import BaseModel
from bson import ObjectId
from bson.objectid import ObjectId as BsonObjectId
from datetime import datetime

class PydanticObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, BsonObjectId):
            raise TypeError('ObjectId required')
        return str(v)
    
class Args(BaseModel):
    output: str
    id: str
    count: int | None

class ClgUserRecord(BaseModel):
    id: PydanticObjectId
    time: datetime

class Challenge(BaseModel):
    score: float
    passed: list[ClgUserRecord]

class Competition(BaseModel):
    challenges: list[Challenge]

class UserModel(BaseModel):
    no: str
    username: str

if __name__ == '__main__':
    parser = ArgumentParser(description='输出比赛的加分信息')
    parser.add_argument('--id', '-i', type=str, required=True, help='比赛的ID')
    parser.add_argument("--output", '-o', default='./output.csv',required=False, type=str, help='统计表格的输出路径')
    parser.add_argument('--count', '-c', default=None, required=False, type=int, help='输出前几名')
    ranks = []
    args = Args(**parser.parse_args().__dict__)
    with MongoClient() as client:
        cols = client.ITA
        comp = cols.competition.find_one({ "_id": ObjectId(args.id) }, {"_id": 1})
        if comp is None:
            print("比赛不存在(ID有误?)")
            exit()
        for rec in sorted(sorted((cols.competition.aggregate([
            {"$match": {"_id": ObjectId(args.id)}},
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
        ])), key=lambda x:x['score'], reverse=True), key=lambda x: x['avg_time'], reverse=True):
            user = cols.user_info.find_one({"_id": rec['_id']}, {
                "no": 1,
                'username': 1,
                '_id': 0,
            })
            ranks.append(user)
    import pandas as pd
    df = pd.DataFrame(ranks)
    df.to_csv(args.output)
    print("Ok")
