import logging
import config
import db
from minterbiz.sdk import Wallet
import time
from pyrogram import Client, Filters, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import threading
import emojis
import tg_analytic
import json
import cache
from utils import *
from filters import *
logging.basicConfig(filename="logs.txt", 
                    format='%(asctime)s %(message)s', 
                    filemode='a') 
logger=logging.getLogger() 
app = Client(
    "my_bot",
    config.api_id, config.api_hash,
    bot_token=config.token
)

sleeping_time = 15

home_markup = ReplyKeyboardMarkup([["Balance","Spend"],["Top up","How to use?"]],resize_keyboard=True)
help_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Add LIKE bot to your group", url="https://t.me/minterlikebot?startgroup=hbase")]])

@app.on_message(Filters.command(["start"]) & Filters.private)
def send_welcome(client,message):
    tg_analytic.statistics(message.chat.id,"start")
    app.send_message(message.chat.id,f"Hi! Get LIKEs in groups and spend on anything.\n\nFor group owner: Add @MinterLikeBot to your group to get 10% of each transaction.",reply_markup=home_markup)
        
def delete_message(chatid,message_id,timeout=sleeping_time):
    global sleeping_time
    time.sleep(timeout)
    app.delete_messages(chatid, message_id)

@app.on_message((Filters.regex("How to use?") & Filters.private) | Filters.command(["help","help@MinterLikeBot"]))
def send_welcomea(client,message):    
    a = app.send_message(message.chat.id,"Send an emoji, sticker or GIF in reply to a message to give 1 LIKE coin to user. Send 2 emojis to give 10 LIKE, 3 and more – 100 LIKE coins\n\nTo send more than 100 LIKE reply with:\nlike X\nThere X is a number between 1-1000\n\nGroup owner gets 10% of every transaction.\n\nAdd @MinterLikeBot to your public group so users can start to interact.",reply_markup=help_markup)
    if message.chat.type == "group" or message.chat.type == "supergroup":
        threading.Thread(target=delete_message,args=(message.chat.id,message.message_id,1)).start()
        threading.Thread(target=delete_message,args=(a.chat.id,a.message_id)).start()

@app.on_message((Filters.regex("Balance") | Filters.command(["balance"])) & Filters.private)
def send_welcomeaa(client,message):
    tg_analytic.statistics(message.chat.id,"balance")
    data = db.create_user(message.chat.id)
    balance = round(cache.get_balance(message.chat.id))
    usd = round(cache.get_price() * float(balance) * cache.get_price_like(),2)
    app.send_message(message.chat.id,f"You've got {balance} LIKE.\nThat's about ${usd}",reply_markup=help_markup)

@app.on_message((Filters.command(['topup']) | Filters.regex("Top up")) & Filters.private)
def topup(client,message):
    tg_analytic.statistics(message.chat.id,"topup")
    data = db.create_user(message.chat.id)
    keyboard_markup = InlineKeyboardMarkup([[InlineKeyboardButton("QR Code", callback_data="qr_code"),InlineKeyboardButton("Address", callback_data="address"),InlineKeyboardButton("BIP Wallet", url=data[-1])]])
    app.send_message(message.chat.id,f"To top up your balance use one of the following options.\n\n<i>Hint: You've got to know a bit about crypto or ask your friend to help.</i>",parse_mode="html",reply_markup=keyboard_markup)

#Handler to Likes Messages with Emoji
@app.on_message((Filters.create((lambda _, message: is_emoji(message.text) > 0)) | Filters.sticker | Filters.animation)  & ~Filters.edited & ~Filters.private)
def like_detect(client,message):
    x = threading.Thread(target=like_d, args=(client,message))
    x.start()

def like_d(client,message): #For asynchronity because Minter SDK doesnt support asyncio
    add_message_to_cache(message)
    tg_analytic.statistics_chat(message.chat.id,get_title_chat(message))
    if message.reply_to_message  and not "edit_date" is message and message.reply_to_message.from_user.id != message["from_user"]["id"] and not message["reply_to_message"]["from_user"]["is_bot"]:
        owner_chat = get_owner_chat(app,message) #Get owner chat for sending commision
        count_emoji = correct_count_emoji(is_emoji(message.text)) #Get count like for detect how many need send
        value_to_send = correct_value_to_send(10 ** (count_emoji - 1)) #Correct if count emoji < 1
        user = db.create_user(message["from_user"]["id"]) #Get user from whom will send LIKE
        user_balance = db.get_balance(message["from_user"]["id"]) #Get balance user
        value_to_send = correct_value_balance(float(value_to_send),float(user_balance)) 
        wallet = Wallet(seed=db.get_mnemo(message["from_user"]["id"])) #Wallet of user
        to_address = db.create_user(message["reply_to_message"]["from_user"]["id"]) 
        if owner_chat != None:#Check if owner exists
            owner_dat = db.create_user(owner_chat.user.id)
            if wallet.address == owner_dat[2] or owner_dat[2] == to_address[2]: #Check if like sending to owner of group or from him
                owner_chat = None
         
        if owner_chat != None: #If owner exists send to him some LIKE
            wallet.send(to=owner_dat[2],value=0.1 * value_to_send, coin="LIKE", payload='', include_commission=True)
            transaction = wallet.send(to=to_address[2],value=0.9 * value_to_send, coin="LIKE", payload='', include_commission=True)
        else:
            transaction = wallet.send(to=to_address[2],value=value_to_send, coin="LIKE", payload='', include_commission=True)

        if transaction != None:
            if not 'error' in transaction["result"]: #If result success send message to chat
                tg_analytic.statistics(message.chat.id,"emoji like",True,value_to_send)
                a = message["reply_to_message"].reply_text("Your message was liked by " + get_name(message) + "! [Spend your coins](https://t.me/MinterLikeBot)",parse_mode="Markdown",disable_web_page_preview=True)
                threading.Thread(target=delete_message,args=(a.chat.id,a.message_id)).start() #Delete message

@app.on_message((Filters.create(lambda _, message:  filter_like_message(message.text))) & ~Filters.edited & ~Filters.private)
def like(client,message):
    x = threading.Thread(target=like_ddd, args=(client,message))
    x.start()

def like_ddd(client,message):
    global caches
    userid = message["from_user"]["id"]
    add_message_to_cache(message)
    tg_analytic.statistics_chat(message.chat.id,get_title_chat(message))
    value_to_send = int(message.text.split(" ")[1])
    if message.reply_to_message.from_user.id != message["from_user"]["id"] and not message["reply_to_message"]["from_user"]["is_bot"] and value_to_send > 0:
        mnemonic = db.get_mnemo(userid)
        wallet = Wallet(seed=mnemonic)
        balance = db.get_balance(userid)
        value_to_send = correct_value_balance(value_to_send,balance)
        owner = get_owner_chat(app,message)
        to_address = db.create_user(message.reply_to_message.from_user.id)
        if owner != None:
            owner_dat = db.create_user(owner.user.id)
            if wallet.address == owner_dat[2] or owner_dat[2] == to_address[2]: #Check if like sending to owner of group or from him
                owner = None
            else:
                wallet.send(to=owner_dat[2],value=0.1 * float(value_to_send), coin="LIKE", payload='', include_commission=True)              
        if owner == None:
            transaction = wallet.send(to=to_address[2],value=float(value_to_send), coin="LIKE", payload='', include_commission=True)
        else:
            transaction = wallet.send(to=to_address[2],value=0.9 * float(value_to_send), coin="LIKE", payload='', include_commission=True)
        if transaction != None:
            if not 'error' in transaction["result"]: #If result success send message to chat
                a = message["reply_to_message"].reply_text("Your message was liked by  " + get_name(message) + "'s message! [Spend your coins](https://t.me/MinterLikeBot)",parse_mode="Markdown",disable_web_page_preview=True)
                tg_analytic.statistics(message.chat.id,"emoji like",True,value_to_send)
                threading.Thread(target=delete_message,args=(a.chat.id,a.message_id)).start()
                
@app.on_message((Filters.regex("Spend") | Filters.command(['spend'])) & Filters.private)
def inline_kb_answer_callback_handleraa(client,message):
    tg_analytic.statistics(message.chat.id,"spend")
    data = cache.get_tap_mn_push(message)
    data1 = cache.get_tap_minter_push(message)
    app.send_message(message.chat.id, f"Your LIKEs are like money, spend on anything:",parse_mode="Markdown",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Tap mn",url=f"https://tap.mn/{data}")],[InlineKeyboardButton("Minterpush",url=data1)]]))

@app.on_message(Filters.create(lambda _, message:  filters_commands(message)) & ~Filters.private)
def del_spam(client,a):
    tg_analytic.statistics(message.chat.id,"spam")
    threading.Thread(target=delete_message,args=(a.chat.id,a.message_id,0)).start()

@app.on_callback_query(Filters.callback_data("address"))
def address(client, query):
    answer_data = query.data
    data = db.create_user(query.from_user.id)[2]
    app.send_message(query.from_user.id, f"`{data}`",parse_mode="Markdown")

@app.on_callback_query(Filters.callback_data("qr_code"))
def inline_kb_answer_callback_handlera(client, query):
    global back_markup
    answer_data = query.data
    data = db.get_qr_code(query.from_user.id)
    app.send_photo(query.from_user.id,data, caption="Scan this QR with camera.")


@app.on_message(Filters.regex("Статистика") & Filters.private)
def statistic(client,message):
    app.send_message(message.chat.id,tg_analytic.custom(app))

if __name__ == '__main__':
    logger.info("Start Bot")
    app.run()
