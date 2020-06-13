import logging
import config
import db
import qrcode
from emoji import UNICODE_EMOJI
from minterbiz.sdk import Wallet
import random
import time
import requests
from mintersdk.minterapi import MinterAPI
from pyrogram import Client, Filters
from pyrogram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import threading
import emojis
import tg_analytic
from pycoingecko import CoinGeckoAPI
cg = CoinGeckoAPI()

app = Client(
    "my_bot",
    config.api_id, config.api_hash,
    bot_token=config.token
)
sleeping_time = 15
api = MinterAPI(api_url="http://api.mtools.network")
caches = dict(messages={},tap_mn={},balance={},pricebip=[float(cg.get_price(ids='bip', vs_currencies='usd')["bip"]["usd"]),time.time()],pricelike=[float(api.estimate_coin_buy("BIP", 1, "LIKE", pip2bip=True)["result"]["will_pay"]),time.time()])

# back_markup = types.InlineKeyboardMarkup(row_width=3)
# back_markup.add(types.InlineKeyboardButton("<= Back", callback_data="back"))
home_markup = ReplyKeyboardMarkup([["Balance","Spend"],["Top up","How to use?"]],resize_keyboard=True)

def get_tap_mn_push(message):
    if not message.chat.id in caches["tap_mn"]:
        caches["tap_mn"][message.chat.id] = requests.post("https://push.minter-scoring.space/api/new",data=dict(seed=db.get_mnemo(message.chat.id))).json()["link"]
    return caches["tap_mn"][message.chat.id]

def get_price():
    if caches["pricebip"][1] < time.time() - 30 * 60:
        caches["pricebip"][0] = float(requests.get("https://api.bip.dev/api/price").json()["data"]["price"]) / 10000
    return caches["pricebip"][0]

def get_price_like():
    if caches["pricelike"][1] < time.time() - 30 * 60:
        caches["pricelike"][0] = float(api.estimate_coin_buy("BIP", 1, "LIKE", pip2bip=True)["result"]["will_pay"])
    return caches["pricelike"][0]

def get_balance(chatid):
    if not chatid in caches["balance"]:
        caches["balance"][chatid] = [db.get_balance(chatid),time.time()]
    else:
        if caches["balance"][chatid][1] < time.time() - 60 * 1:
            caches["balance"][chatid] = [db.get_balance(chatid),time.time()]
    return caches["balance"][chatid][0]

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


def get_owner_chat(message):
    a = app.get_chat_members(message.chat.id, filter="administrators")
    owner = None
    for i in a:
        print(i["status"],i["status"] == "creator")
        if i["status"] == "creator":
            owner = i
    print(owner)
def get_owner_chat_l(message):
    a = app.get_chat_members(message.chat.id, filter="administrators")
    owner = None
    for i in a:
        print(i["status"],i["status"] == "creator")
        if i["status"] == "creator":
            owner = i
    print(owner)

@app.on_message(Filters.command(["start"]) & Filters.private)
def send_welcome(client,message):

    print(message)
    if message.chat.type == "private":
        tg_analytic.statistics(message.chat.id,"start")
        """
        This handler will be called when user sends `/start` or `/help` command
        """
        #data = db.create_user(message.chat.id)
        # img = qrcode.make(data[1])
        # print(type(img))
        
        #keyboard_markup.add(types.InlineKeyboardButton("QR Code", callback_data="qr_code"),
        #                    types.InlineKeyboardButton("⚠️Mnemonic⚠️", callback_data="mnemo"),
        #                    types.InlineKeyboardButton("Open in BIP Wallet", url=data[-1]),
        #                    types.InlineKeyboardButton("Send PUSH", callback_data="push"),
        #    )
        #print(message.chat.id)
        #balance = round(db.get_balance(message.chat.id),2)
        print(message.chat.id)
        app.send_message(message.chat.id,f"Hi! Get LIKEs in groups and spend on anything.\n\nFor group owner: Add @MinterLikeBot to your group to get 10% of each transaction.",reply_markup=home_markup)
        
    elif message.chat.type == "group" or message.chat.type == "supergroup":
        add_message_to_cache(message)
        # owner = None
        # for i in await message.chat.get_administrators():
        #     if i.status == "creator":
        #         owner = i.user.first_name
        # await message.answer(f"🤖 Working....\n" + owner  )
def delete_message(chatid,message_id,timeout=sleeping_time):
    global sleeping_time
    time.sleep(timeout)
    app.delete_messages(chatid, message_id)
@app.on_message(Filters.command(["help","help@MinterLikeBot"]))
@app.on_message(Filters.regex("How to use?") & Filters.private)
def send_welcomea(client,message):
    
    keyboard_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Add LIKE bot to your group", url="https://t.me/minterlikebot?startgroup=hbase")]])
    a = app.send_message(message.chat.id,"Send an emoji, sticker or GIF in reply to a message to give 1 LIKE coin to user. Send 2 emojis to give 10 LIKE, 3 and more – 100 LIKE coins\n\nTo send more than 100 LIKE reply with:\nlike X\nThere X is a number between 1-1000\n\nGroup owner gets 10% of every transaction.\n\nAdd @MinterLikeBot to your public group so users can start to interact.",reply_markup=keyboard_markup)
    if message.chat.type == "group" or message.chat.type == "supergroup":
        threading.Thread(target=delete_message,args=(message.chat.id,message.message_id,1)).start()
        threading.Thread(target=delete_message,args=(a.chat.id,a.message_id)).start()

@app.on_message(Filters.command(["balance"]) & Filters.private)
@app.on_message(Filters.regex("Balance") & Filters.private)
def send_welcomeaa(client,message):
    if message.chat.type == "private":
        tg_analytic.statistics(message.chat.id,"balance")
        data = db.create_user(message.chat.id)
        
        balance = round(get_balance (message.chat.id))
        usd = round(get_price() * float(balance) * get_price_like(),2)
        
        keyboard_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Add LIKE bot to your group", url="https://t.me/minterlikebot?startgroup=hbase")]])
        app.send_message(message.chat.id,f"You've got {balance} LIKE.\nThat's about ${usd}",reply_markup=keyboard_markup)
    else:
        threading.Thread(target=delete_message,args=(message.chat.id,message.message_id,1)).start()

@app.on_message(Filters.command(['topup']) & Filters.private)
@app.on_message(Filters.regex("Top up") & Filters.private)
def topup(client,message):
    if message.chat.type == "private":
        tg_analytic.statistics(message.chat.id,"topup")
        data = db.create_user(message.chat.id)
        keyboard_markup = InlineKeyboardMarkup([[InlineKeyboardButton("QR Code", callback_data="qr_code"),InlineKeyboardButton("Address", callback_data="address"),InlineKeyboardButton("BIP Wallet", url=data[-1])]])

        app.send_message(message.chat.id,f"To top up your balance use one of the following options.\n\n<i>Hint: You've got to know a bit about crypto or ask your friend to help.</i>",parse_mode="html",reply_markup=keyboard_markup)
    else:
        threading.Thread(target=delete_message,args=(message.chat.id,message.message_id,1)).start()
@app.on_message((Filters.create((lambda _, message: is_emoji(message.text) > 0)) | Filters.sticker | Filters.animation)  & ~Filters.edited)
def like_detect(client,message):
    
    x = threading.Thread(target=like_d, args=(client,message))
    x.start()


def like_d(client,message):
    if (message.chat.type == "group" or message.chat.type == "supergroup"):

        add_message_to_cache(message)
        if message.reply_to_message  and not "edit_date" is message:
            if message.reply_to_message.from_user.id != message["from_user"]["id"] and not message["reply_to_message"]["from_user"]["is_bot"]:
                owner = get_owner_chat_l(message)

                count_emoji = is_emoji(message.text)
                print(count_emoji)
                if count_emoji > 3:
                    count_emoji = 3
                count_emoji = count_emoji - 1
                
                c = 10 ** count_emoji
                if c < 1:
                    c = 1
                print(c)
                user = db.create_user(message["from_user"]["id"])

                user_balance = db.get_balance(message["from_user"]["id"])
                if float(user_balance) > c:
                    co = c
                else:
                    co = float(user_balance)
                    co = co - 0.01
                print(db.get_mnemo(message["from_user"]["id"]))
                wallet = Wallet(seed=db.get_mnemo(message["from_user"]["id"]))
                dat = db.create_user(message["reply_to_message"]["from_user"]["id"])
                if owner != None:
                    owner_dat = db.create_user(owner.id)
                    if wallet.address == owner_dat[2] or owner_dat[2] == dat[2]:
                        owner = None
                if owner != None:
                    wallet.send(to=owner_dat[2],value=0.1 * co, coin="LIKE", payload='', include_commission=True)
                    d = wallet.send(to=dat[2],value=0.9 * co, coin="LIKE", payload='', include_commission=True)
                else:
                    print(co)
                    d = wallet.send(to=dat[2],value=co, coin="LIKE", payload='', include_commission=True)

                if d != None:
                    if not 'error' in d["result"]:
                        tg_analytic.statistics(message.chat.id,"emoji like",True,co)
                        a = message["reply_to_message"].reply_text("Your message was liked by " + get_name(message) + "! [Spend your coins](https://t.me/MinterLikeBot)",parse_mode="Markdown",disable_web_page_preview=True)
                        threading.Thread(target=delete_message,args=(a.chat.id,a.message_id)).start()


@app.on_message(Filters.command(['spend']) & Filters.private)
@app.on_message(Filters.regex("Spend") & Filters.private)
def inline_kb_answer_callback_handleraa(client,message):
    tg_analytic.statistics(message.chat.id,"spend")
    global back_markup
    data = get_tap_mn_push(message)
    if data != None:
        app.send_message(message.chat.id, f"Your LIKEs are like money, spend on anything:",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Go to wallet",url=f"https://tap.mn/{data}")]]))
    else:
        app.send_message(message.chat.id, "Some Error\nMaybe not enough money to send transaction",parse_mode="Markdown")


def a(message):
    try:
        lists = ["start","balance","spend","topup"]
        for i in lists:
            if "/" + i + "@MinterLikeBot" in message.text:
                return True
        return False
    except:
        return False

@app.on_message(Filters.create(lambda _, message:  a(message)) & ~Filters.private)
def delets(client,a):
    threading.Thread(target=delete_message,args=(a.chat.id,a.message_id,0)).start()

@app.on_callback_query(Filters.callback_data("address"))
def address(client, query):
    global back_markup
    answer_data = query.data
    data = db.create_user(query.from_user.id)[2]
    app.send_message(query.from_user.id, f"`{data}`",parse_mode="Markdown")

@app.on_callback_query(Filters.callback_data("qr_code"))
def inline_kb_answer_callback_handlera(client, query):
    global back_markup
    answer_data = query.data
    data = db.get_qr_code(query.from_user.id)
    app.send_photo(query.from_user.id,data, caption="Scan this QR with camera.")

@app.on_message(Filters.group)
def liked(client, message):
    add_message_to_cache(message)

@app.on_message(Filters.regex("Статистика") & Filters.private)
def statistic(client,message):
    app.send_message(message.chat.id,tg_analytic.custom(app))


if __name__ == '__main__':
    app.run()
