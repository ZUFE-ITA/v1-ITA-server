# from gridfs import GridFS

# from .includes import *

# class FileSystem:

#     def __init__(self, coll_name) -> None:
#         self.gridfs = GridFS(db, coll_name)

#     async def upload(self, content_type: str, data: bytes, hash: str):
#         info = {
#             "content_type": content_type,
#             "hash": hash
#         }
#         if not self.gridfs.exists({"hash": hash}):
#             file_ = self.gridfs.put(data, **info)

#     async def download(self, hash: str):
#         data = self.gridfs.find_one({"hash": hash})
#         return data


# class File:

#     fs = FileSystem("file")

#     @classmethod
#     async def store(cls, content_type: str, data: bytes, hash: str):
#         await cls.fs.upload(content_type, data, hash)

#     @classmethod
#     async def load(cls, hash: str):
#         return await cls.fs.download(hash)

