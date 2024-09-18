import sys
import os
from pathlib import Path

# 获取当前脚本所在的目录
current_dir = Path(__file__).parent

if current_dir not in sys.path:
    sys.path.insert(0, current_dir.parent.absolute().as_posix())
print(current_dir.parent.absolute().as_posix())

import meo
from app.utils.permission import parse_permission

users = meo.load_json(current_dir.joinpath("./data/user_info.json"))


for user in users:
    pm = parse_permission(user.get("permission"))
    user["permission"] = pm.dict()

meo.to_json(users, current_dir.joinpath("./data/user_info.json"), indent=4, ensure_ascii=False)