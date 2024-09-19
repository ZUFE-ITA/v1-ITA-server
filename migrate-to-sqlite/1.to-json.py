import bson
import json
import sys

from pathlib import Path
from bson import ObjectId
from datetime import datetime

current_dir = Path(__file__).parent

if current_dir not in sys.path:
    sys.path.insert(0, current_dir.parent.absolute().as_posix())

from app.utils.permission import parse_permission

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        return super().default(obj)

def to_json_file(data, path: str):
    with open(path, "w+") as json_file:
        json.dump(
            data, json_file, indent=4, cls=CustomJSONEncoder, ensure_ascii=False
        )

def bson_to_json(input_bson_path, output_json_path = None):
    with open(input_bson_path, "rb") as bson_file:
        bson_data = bson_file.read()

    documents = bson.decode_all(bson_data)
    if output_json_path is None:
        return documents
    to_json_file(documents, output_json_path)


def objectid_to_unix(oid: ObjectId):
    timestamp = oid.generation_time
    unix_timestamp = int(timestamp.timestamp())
    return unix_timestamp

if __name__ == "__main__":
    bson_to_json("./dump/challenge.bson", "./data/challenge.json")
    bson_to_json("./dump/competition.bson", "./data/competition.json")
    bson_to_json("./dump/config.bson", "./data/config.json")
    bson_to_json("./dump/event.bson", "./data/event.json")
    bson_to_json("./dump/user_event_history.bson", "./data/user_event_history.json")
    bson_to_json("./dump/team_mail.bson", "./data/team_mail.json")
    
    users = bson_to_json("./dump/user_info.bson")
    for user in users:
        pm = parse_permission(user.get("permission"))
        user["permission"] = pm.model_dump()
    to_json_file(users, "./data/user_info.json")
