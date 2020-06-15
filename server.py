from flask import Flask
from flask import render_template
app = Flask(__name__)
import tg_analytic

class chat(object):
    name = None
    likes_sended = None
    messages = None
    def __init__(self, id):
        self.id = id
    def gets_data(self):
        return tg_analytic.get_chat(self.id)
        

@app.route('/')
def hello_world():
    chats_list = tg_analytic.get_chats()
    r = []
    for i in chats_list:
        r.append(tg_analytic.get_chat(i))
    return  render_template('index.html',r=r)

@app.route('/stats')
def stats():
    chats_list = tg_analytic.custom(foo=False)
    print(chats_list)

    return  render_template('stats.html',stats=chats_list)


if __name__ == '__main__':
    app.run()