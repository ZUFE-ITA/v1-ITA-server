from pydantic import BaseModel
from enum import Enum

class BasePermissionModel(BaseModel):
    Append:        bool
    Vet:           bool
    DeleteSelf:   bool
    DeleteOthers: bool
    Read:          bool

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
    Append = 'a'
    Vet = 'v'
    DeleteSelf = 'd'
    DeleteOthers = 'D'
    Join = 'j'

class Blog(Enum):
    Read = 'r'
    Append = 'a'
    Vet = 'v'
    DeleteSelf = 'd'
    DeleteOthers = 'D'

class Challenge(Enum):
    Read = 'r'
    Append = 'a'
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
# class PermissionModel:
    
#     Blog = Blog
#     Event = Event

#     def __init__(self, permission=DEFAULT_PERMISSION) -> None:
#         self.permission = permission
#         self.group = permission.split(";")

#     @classmethod
#     def make_str(cls, *permission: Blog|Event):
#         return cls.add(DEFAULT_PERMISSION, *permission)

#     @classmethod
#     def add(cls, origin: str,  *permission: Blog|Event):
#         event, blog = map(list, origin.split(";"))
#         for p in permission:
#             match p:
#                 case Blog.Read:
#                     blog[0] = Blog.Read.value
#                 case Blog.Append:
#                     blog[1] = Blog.Append.value
#                 case Blog.Vet:
#                     blog[2] = Blog.Vet.value
#                 case Blog.DeleteSelf:
#                     blog[3] = Blog.DeleteSelf.value
#                 case Blog.DeleteOthers:
#                     blog[4] = Blog.DeleteOthers.value

#                 case Event.Read:
#                     event[0] = Event.Read.value
#                 case Event.Append:
#                     event[1] = Event.Append.value
#                 case Event.Vet:
#                     event[2] = Event.Vet.value
#                 case Event.DeleteSelf:
#                     event[3] = Event.DeleteSelf.value
#                 case Event.DeleteOthers:
#                     event[4] = Event.DeleteOthers.value
#                 case Event.Join:
#                     event[5] = Event.Join.value

#         return ";".join(("".join(event), "".join(blog)))

#     def get_groups(self, idx):
#         if len(self.group) < idx:
#             return DEFAULT_GROUPS[idx]
#         return self.group[idx]

#     @property
#     def event_permission(self):
#         """ `Event`是`0 group` """
#         return self.get_groups(0)
    
#     @property
#     def blog_permission(self):
#         return self.get_groups(1)

#     def check_grant_request(self, request: str):
#         '''`request`和`self.permission`类似'''
#         for i, w in enumerate(request):
#             if w != '-' and self.permission[i] == '-':
#                 return False
#         return True

#     def can(self, op: Blog | Event):
#         if op in Blog:
#             return op.value in self.blog_permission
#         elif op in Event:
#             return op.value in self.event_permission
#         return False

#     def cannot(self, op: Blog|Event):
#         return not self.can(op)


if __name__ == "__main__":
    sss = 'r-----'
    res = parse_permission(sss)
    print(res.json(indent=4))
    # model = PermissionModel("r-----;ra---")
    # print(model.check_grant_request("-----j;-----"))
    # per = PermissionModel.make_str(Event.Join, Event.Append)
    # print(per)
    # print(PermissionModel.add(per, Blog.Vet))
    # print(Event.Append in Blog)
