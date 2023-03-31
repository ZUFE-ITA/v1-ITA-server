from pydantic import BaseModel
from enum import Enum

class BasePermissionModel(BaseModel):
    Read:          bool
    Vet:           bool
    Write:         bool
    DeleteSelf:    bool
    DeleteOthers:  bool

class BlogPermissionModel(BasePermissionModel):
    pass

class EventPermissionModel(BasePermissionModel):
    Join: bool

class ChallengePermissionModel(BasePermissionModel):
    pass

class PermissionModel(BaseModel):
    Blog: BlogPermissionModel
    Event: EventPermissionModel
    Challenge: ChallengePermissionModel


DEFAULT_PERMISSION = "r----j;r----;-----"
DEFAULT_GROUPS = DEFAULT_PERMISSION.split(';')

"""
权限检测
"""
class Event(Enum):
    Read = 'r'
    Write = 'w'
    Vet = 'v'
    DeleteSelf = 'd'
    DeleteOthers = 'D'
    Join = 'j'

class Blog(Enum):
    Read = 'r'
    Write = 'w'
    Vet = 'v'
    DeleteSelf = 'd'
    DeleteOthers = 'D'

class Challenge(Enum):
    Read = 'r'
    Write = 'w'
    Vet = 'v'
    DeleteSelf = 'd'
    DeleteOthers = 'D'

def parse_permission(perm: str = None):
    if perm is None:
        group = DEFAULT_GROUPS
    else:
        group = perm.split(";")
        if len(group) < len(DEFAULT_GROUPS):
            group += DEFAULT_GROUPS[len(group): ]
    fields = [
        (Event, 'Event'), 
        (Blog, 'Blog'), 
        (Challenge, 'Challenge')
    ]
    collect = {}
    for (check, key), g in zip(fields, group):
        tmp = collect[key] = {}
        for idx, field in enumerate(check):
            name = field.name
            code = g[idx] == field.value
            tmp[name] = code
    return PermissionModel(**collect)

if __name__ == "__main__":
    sss = 'r-----'
    res = parse_permission(sss)
    print(res.json(indent=4))
    