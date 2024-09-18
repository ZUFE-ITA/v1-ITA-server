import bson
import json

from bson import ObjectId
from datetime import datetime


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, bytes):
            return str(obj)
        return super().default(obj)


def bson_to_json(input_bson_path, output_json_path):
    with open(input_bson_path, "rb") as bson_file:
        bson_data = bson_file.read()

    decoded_data = bson.decode_all(bson_data)

    with open(output_json_path, "w+") as json_file:
        json.dump(
            decoded_data, json_file, indent=4, cls=CustomJSONEncoder, ensure_ascii=False
        )


if __name__ == "__main__":
    bson_to_json("./dump/challenge.bson", "./data/challenge.json")
    bson_to_json("./dump/competition.bson", "./data/competition.json")
    bson_to_json("./dump/config.bson", "./data/config.json")
    bson_to_json("./dump/event.bson", "./data/event.json")
    bson_to_json("./dump/user_event_history.bson", "./data/user_event_history.json")
    bson_to_json("./dump/user_info.bson", "./data/user_info.json")
    bson_to_json("./dump/team_mail.bson", "./data/team_mail.json")
