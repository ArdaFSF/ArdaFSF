from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return "Alive"

def run():
    print("[KEEP_ALIVE] Flask sunucusu başlatılıyor...")
    app.run(host='0.0.0.0', port=8080)
    print("[KEEP_ALIVE] Flask sunucusu durdu.")  # Bu satıra normalde gelmezsin.

def keep_alive():
    print("[KEEP_ALIVE] Thread başlatılıyor...")
    t = Thread(target=run)
    t.start()
    print("[KEEP_ALIVE] Flask thread'i çalışıyor.")
