import secrets

from .includes import *

class Config:
    
    collection = db.config

    @classmethod
    async def properties(cls) -> dict:
        p = await cls.collection.find_one({})
        if p:
            return p
        return {}

    @classmethod
    async def update(cls, config: dict):
        return await cls.collection.update_one({}, {
            "$set": config
        }, upsert=True)

    @classmethod
    async def secret_key(cls):
        key = r.get_token_key()
        if key is None:
            properties = await cls.properties()
            key = properties.get("secret_key", None)
            if key is None:
                key = secrets.token_hex(32)
                await cls.update({"secret_key": key})
            r.set_token_key(key)
        return key
