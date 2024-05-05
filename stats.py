#!/usr/bin/env python
from pymongo import MongoClient
from pymongo.database import Database
import pymongo.collection
from argparse import ArgumentParser
from pydantic import BaseModel
from bson import ObjectId
from bson.objectid import ObjectId as BsonObjectId
from datetime import datetime
import os


class PydanticObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, BsonObjectId):
            raise TypeError("ObjectId required")
        return str(v)


class Args(BaseModel):
    output: str | None
    id: str | None
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


def select_competition(db: Database):
    from tabulate import tabulate

    tb = []
    header = ["idx", "title", "desc", "id"]
    mapping = {}
    for idx, rec in enumerate(db.competition.find({}, {"_id": 1})):
        _id = rec["_id"]
        event = db.event.find_one({"_id": _id})
        desc = event.get("desc", "")
        title = event.get("title", "")
        tb.append([idx, title, desc, str(_id)])
        mapping[idx] = str(_id)
    print(tabulate(tb, header))
    return mapping[int(input("需要统计的比赛编号: "))]


if __name__ == "__main__":
    parser = ArgumentParser(description="输出比赛的加分信息")
    parser.add_argument(
        "--id", "-i", type=str, default=None, required=False, help="比赛的ID"
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        required=False,
        type=str,
        help="统计表格的输出路径",
    )
    parser.add_argument(
        "--count", "-c", default=None, required=False, type=int, help="输出前几名"
    )
    ranks = []
    args = Args(**parser.parse_args().__dict__)
    with MongoClient() as client:
        # 没有id则进入选择id
        cols = client.ITA
        args.id = select_competition(cols)
        comp = cols.competition.find_one({"_id": ObjectId(args.id)}, {"_id": 1})
        if comp is None:
            print("比赛不存在(ID有误?)")
            exit()
        for rec in sorted(
            (
                cols.competition.aggregate(
                    [
                        {"$match": {"_id": ObjectId(args.id)}},
                        {"$unwind": "$challenges"},
                        {"$unwind": "$challenges.passed"},
                        {
                            "$group": {
                                "_id": "$challenges.passed.id",
                                "count": {"$sum": 1},
                                "score": {"$sum": "$challenges.score"},
                                "avg_time": {
                                    "$avg": {"$toLong": "$challenges.passed.time"}
                                },
                            }
                        },
                    ]
                )
            ),
            key=lambda x: (x["score"], x["count"], -x["avg_time"]),
            reverse=True,
        )[: args.count if args.count is not None else -1]:
            user = cols.user_info.find_one(
                {"_id": rec["_id"]},
                {
                    "no": 1,
                    "username": 1,
                    "_id": 0,
                },
            )
            ranks.append(user)

    import pandas as pd

    df = pd.DataFrame(ranks)
    if output := args.output is None:
        OUTPUT_DIR = "./output"
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        output = os.path.join(OUTPUT_DIR, f"{args.id}.csv")
    df.to_csv(output)
    print("Ok")
