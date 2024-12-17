from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
import httpx
import asyncio
import time

with open("token") as f:
    BOT_TOKEN = f.read().strip()

app = FastAPI()
http_client = httpx.AsyncClient(timeout=30)
executor = ThreadPoolExecutor(max_workers=20)
# Replace with your bot's token
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEB_SERVER_URL = "cossmo.alwaysdata.net"
WEB_HOOK_SERVER_ENDPOINT = WEB_SERVER_URL + "/handle_webhook"

MAX_TIME = 60
def get_send_msg_url(chat_id:int):
    return f"{TELEGRAM_API_URL}/sendMessage?chat_id={chat_id}&text="


async def send_msg(msg: str, chat_id:int):
    url = get_send_msg_url(chat_id)
    await http_client.get(url, params={'chat_id': chat_id, 'text':msg})

def send_msg_sync(msg: str, chat_id:int):
    url = get_send_msg_url(chat_id)
    httpx.get(url, params={'chat_id': chat_id, 'text': msg})

def get_telegram_webhook_url():
    return f"{TELEGRAM_API_URL}/setWebhook"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.on_event("shutdown")
async def on_shutdown():
    await http_client.aclose()
    print('app is shut down.')


@app.on_event("startup")
async def set_webhook():
    response = await http_client.post(
        get_telegram_webhook_url(),
        json={"url": WEB_HOOK_SERVER_ENDPOINT},
    )
    print(f"Webhook set: {response.json()}")


@app.post("/handle_webhook")
async def handle_webhook(request: Request):
    return {"status": "OK"}
    """
    Handle incoming Telegram messages.
    """
    def long_function(n, val, chat_id):
        st_time = time.time()
        result = 0

        for i in range(10 ** n):
            if i % 100000 == 0:
                end_time = time.time()
                if end_time-st_time > MAX_TIME:
                    send_msg_sync(f"Ответ на {val}: время работы превышено", chat_id)
                    return
            result += 1
        send_msg_sync(f"Ответ на {val}: {result}", chat_id)

    data = await request.json()
    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]
    try:
        val = int(text)
        await send_msg(f"Вы написали {val}, мы работаем...", chat_id)
        asyncio.create_task(asyncio.to_thread(long_function, val, chat_id))

        return {"status": "OK"}
    except ValueError:
        await send_msg(f"Некорректное число: {text}", chat_id)
        return {"status": "Bad Request"}


# Example endpoint to verify it's running
@app.get("/")
async def read_root():
    return {"message": "FastAPI Telegram Webhook is running!"}
