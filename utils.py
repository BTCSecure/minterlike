import emojis
from cache import caches


def get_title_chat(message):
    return message.chat.title


def get_name(message):
    name = ""
    name += message["from_user"]["first_name"]
    try:
        message["from_user"]["last_name"]
        name += " "
        name += message["from_user"]["last_name"]
    except:
        pass
    return name


def is_emoji(s):
    try:
        return emojis.count(s)
    except:
        return 0


def add_message_to_cache(message):
    global caches
    try:
        caches["messages"][message.chat.id].append(message)
    except:
        caches["messages"][message.chat.id] = []
        caches["messages"][message.chat.id].append(message)
    if len(caches["messages"][message.chat.id]) == 500:
        caches["messages"][message.chat.id].pop(0)


def get_owner_chat(app, message):
    a = app.get_chat_members(message.chat.id, filter="administrators")
    owner = None
    for i in a:
        print(i["status"], i["status"] == "creator")
        if i["status"] == "creator":
            owner = i
    return owner

correct_value_to_send = lambda a: 1 if a < 1 else a
correct_count_emoji = lambda a: 3 if a > 3 else a
correct_value_balance = lambda will_send, user_balance: float(
    user_balance) - 0.01 if float(will_send) > float(user_balance) + 0.01 else float(will_send)
