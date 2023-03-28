def check_username(name: str):
    """不能有空格 字数不能超过32个"""
    if 1 < len(name) < 32 and ' ' not in name:
        return True
    return False

def check_psw(pwd: str):
    if len(pwd) < 6:
        return False
    return True


if __name__ == "__main__":
    print(check_username("i i i"))