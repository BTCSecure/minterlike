def filters_commands(message):
    try:
        lists = ["start","balance","spend","topup"]
        for i in lists:
            if "/" + i + "@MinterLikeBot" in message.text:
                return True
        return False
    except:
        return False


def filter_like_message(s):
    try:
        return "like " in s.lower()
    except:
        return False	