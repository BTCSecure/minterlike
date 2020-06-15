from pycoingecko import CoinGeckoAPI
import db
from mintersdk.minterapi import MinterAPI
import time
import requests

cg = CoinGeckoAPI()
api = MinterAPI(api_url="http://api.minter.one")
caches = dict(messages={},push={},tap_mn={},balance={},pricebip=[float(cg.get_price(ids='bip', vs_currencies='usd')["bip"]["usd"]),time.time()],pricelike=[float(api.estimate_coin_buy("BIP", 1, "LIKE", pip2bip=True)["result"]["will_pay"]),time.time()])

def get_tap_minter_push(message):
    if not message.chat.id in caches["push"]:
        mnemo = db.get_mnemo(message.chat.id)
        data = json.dumps(dict(seed=mnemo,coin="LIKE"))
        response = requests.post('https://api.minterpush.com/create', headers={'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJtaW50ZXJwdXNoLmNvbSIsImF1ZCI6Im1pbnRlcnB1c2guY29tIiwicm9sIjoiYXBpIiwic3ViIjoiUlJQNzRtaDhpb1pDbWh3eWVQMUtUTEJHIiwiZXhwIjoxNTkzMDI5NDcwfQ.poTy3D1fZDcYpLPlRe1pVK6xCiCjbqHL3CNZbpjrMpUEuHDczEz0Q_p4rqQgh0Ia2HYxRQiA-Pn1RWKpJ2Ihkw','Content-Type': 'application/json'}, data=data)
        caches["push"][message.chat.id] = response.json()["data"]["url"]
    return caches["push"][message.chat.id]

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