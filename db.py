import psycopg2
from mintersdk.sdk.wallet import MinterWallet
import qrcode
import os.path
from mintersdk.minterapi import MinterAPI
from mintersdk.sdk.transactions import MinterSendCoinTx
from mintersdk.sdk.deeplink import MinterDeeplink
import requests
from minterbiz.sdk import Wallet
import config
conn = psycopg2.connect(dbname='minter_like', user=config.db_user, 
                        password=config.db_password, host='localhost')
cursor = conn.cursor()
api = MinterAPI(api_url="http://api.mtools.network")

def repack(chat_id):
    likes = get_balance(chat_id)
    if likes > 0:
        mnemonic = get_mnemo(chat_id)
        data = {
          'seed': mnemonic,
          'name': 'User'
        }
        print(mnemonic)
        print(data)
        a = requests.post('https://push.minter-scoring.space/api/new', data=data).json()
        print(a["address"])
        wallet = Wallet(seed=mnemonic)
        wallet.send(to=a["address"],value=likes, coin="LIKE", payload='', include_commission=True)
        if "link" in a:
            return a["link"]
    return None

def get_balance(chat_id):
    global api
    cursor.execute(f'SELECT address FROM users WHERE chatid = {chat_id};')
    records = cursor.fetchone()
    print(records)
    balance = api.get_balance(records[0],pip2bip=True)
    if 'LIKE' in balance['result']['balance']:
        return balance['result']['balance']['LIKE']
    else:
        return 0

def get_mnemo(chat_id):
    cursor.execute(f'SELECT mnemo FROM users WHERE chatid = {chat_id};')
    records = cursor.fetchone()
    return records[0]

def exists_user(chat_id):
    cursor.execute(f'SELECT * FROM users WHERE chatid = {chat_id};')
    records = cursor.fetchall()
    if len(records) == 1:
        return records[0]
    return None

def exists_chat(chat_id):
    cursor.execute(f'SELECT * FROM chats WHERE chatid = {chat_id};')
    records = cursor.fetchall()
    if len(records) == 1:
        return records[0]
    return None

def get_qr_code(chat_id):
    cursor.execute(f'SELECT address FROM users WHERE chatid = {chat_id};')
    data = cursor.fetchone()
    path = "qr/" + data[0] + ".png"
    if not os.path.isfile(path):
        qr = qrcode.QRCode(
            version=12,
            error_correction=qrcode.constants.ERROR_CORRECT_Q,
            box_size=8,
            border=4
        )
        print(data[0])
        qr.add_data(data[0])
        qr.make()
        img = qr.make_image(fill_color="#D15C22")
        img.save(path)
        file = open(path,'rb')
        img = file.read()
        file.close()
    return path

def create_user(chat_id):
    temp = exists_user(chat_id) 
    if temp == None:
        wallet = MinterWallet.create()
        address = wallet["address"]
        tx = MinterSendCoinTx(coin='LIKE', to=address, value=10, gas_coin='BIP', gas_price=1,nonce=1)
        dl = MinterDeeplink(tx=tx)
        dl.nonce = ''
        dl.value = ''
        url_link = dl.generate()
        cursor.execute('INSERT INTO users (chatid,address,privatekey,mnemo,deeplink) VALUES {};'.format(
            (chat_id, wallet["address"], wallet["private_key"], wallet["mnemonic"],url_link)
        ))
        conn.commit()

        return (chat_id, wallet["address"], wallet["private_key"], wallet["mnemonic"],url_link)
    return temp

def create_chat(chat_id):
    temp = exists_chat(chat_id)
    if temp == None:
        cursor.execute('INSERT INTO users (chatid) VALUES {};'.format(
            (chat_id)
        ))

