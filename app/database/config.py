import secrets

from .includes import *

class Config:
    
    collection = db.config

    @classmethod
    def properties(cls) -> dict:
        p = cls.collection.find_one({})
        if p:
            return p
        return {}

    @classmethod
    def update(cls, config: dict):
        return cls.collection.update_one({}, {
            "$set": config
        }, upsert=True)

    @classmethod
    def secret_key(cls):
        key = r.get_token_key()
        if key is None:
            properties = cls.properties()
            key = properties.get("secret_key", None)
            if key is None:
                key = secrets.token_hex(32)
                cls.update({"secret_key": key})
            r.set_token_key(key)
        return key
