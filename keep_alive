import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang chạy!"

def run():
  # Lấy cổng từ biến môi trường PORT, nếu không có thì dùng 8080 (hoặc 5000)
  port = int(os.environ.get("PORT", 8080))
  app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
