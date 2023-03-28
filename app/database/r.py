# 维护redis数据
import redis

class RedisProvider:

    def __init__(self, host='localhost', port=6379, decode_responses=True) -> None:
        self.r = redis.StrictRedis(host, port=port, decode_responses=decode_responses)
    
    def get_token_key(self):
        return self.r.get("idim:sys:token-key")

    def set_token_key(self, key):
        self.r.set("idim:sys:token-key", key)

    def ttl_verify_code(self, uid: str, code_type: str):
        return self.r.ttl(f"{uid}:verify:{code_type}:code")

    def get_verify_code(self, uid, code_type):
        return self.r.get(f"{uid}:verify:{code_type}:code")
        
    def set_verify_code(self, uid, code, code_type, ex=1800):
        self.r.set(f"{uid}:verify:{code_type}:code", code, ex=ex)

    def get_username(self, uid):
        return self.r.hget("idim:username", uid)
        
    def set_username(self, uid, username):
        self.r.hset("idim:username", uid, username)
