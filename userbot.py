import os
import sys
import json
import traceback
import asyncio
import base64
import requests
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import CreateChannelRequest
from telethon.sessions import StringSession   # <-- Əlavə olundu

# =================== CONFIG ===================
api_id = int(os.getenv("API_ID", "12345"))       # Telegram API_ID
api_hash = os.getenv("API_HASH", "")             # Telegram API_HASH
SESSION_STRING = os.getenv("SESSION_STRING")     # StringSession üçün ENV

if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)
else:
    # Lokalda işlətmək üçün (Render-də istifadə olunmayacaq)
    session_file = os.getenv("SESSION", "user.session")
    client = TelegramClient(session_file, api_id, api_hash)

ADMIN_IDS = [8221469331]  # Admin ID (yalnız sənin üçün işləyəcək)
PLUGINS_FILE = "plugins.json"
ALIVE_FILE = "alive.json"
LOG_FILE = "error.log"
LOG_GROUP_FILE = "loggroup.txt"

SUPPORT_GROUP = "RyhavenSupport"  # support qrupu username (link deyil!)

# =================== GITHUB CONFIG ===================
GITHUB_REPO = os.getenv("GITHUB_REPO", "aliyefhxx/mylayfbombakayf")
GITHUB_FILE = "plugins.json"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# =================== OVERRIDES ===================
old_send = client.send_message
old_edit = client.edit_message

async def new_send(*args, **kwargs):
    if "message" in kwargs:
        kwargs["message"] = f"**{kwargs['message']}**"
        kwargs["parse_mode"] = "markdown"
    elif len(args) > 1:
        args = list(args)
        args[1] = f"**{args[1]}**"
        kwargs["parse_mode"] = "markdown"
    return await old_send(*args, **kwargs)

async def new_edit(*args, **kwargs):
    if "text" in kwargs:
        kwargs["text"] = f"**{kwargs['text']}**"
        kwargs["parse_mode"] = "markdown"
    elif len(args) > 2:
        args = list(args)
        args[2] = f"**{args[2]}**"
        kwargs["parse_mode"] = "markdown"
    return await old_edit(*args, **kwargs)

client.send_message = new_send
client.edit_message = new_edit

# =================== HELPERS ===================
def load_plugins():
    if not os.path.exists(PLUGINS_FILE):
        with open(PLUGINS_FILE, "w", encoding="utf-8") as f:
            json.dump({"plugins": []}, f)
    with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for code in data.get("plugins", []):
        try:
            exec(code, globals())
        except Exception as e:
            asyncio.create_task(send_log(f"PLUGIN XƏTA: {e}\nKod: {code[:50]}..."))

def save_plugin(code):
    with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if code not in data["plugins"]:
        data["plugins"].append(code)
        with open(PLUGINS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def remove_plugin(code):
    with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if code in data["plugins"]:
        data["plugins"].remove(code)
        with open(PLUGINS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def load_alive():
    if not os.path.exists(ALIVE_FILE):
        with open(ALIVE_FILE, "w") as f:
            json.dump({}, f)
    with open(ALIVE_FILE, "r") as f:
        return json.load(f)

def save_alive(data):
    with open(ALIVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def send_log(error_text):
    if not os.path.exists(LOG_GROUP_FILE):
        result = await client(CreateChannelRequest(
            title="Ryhaven Userbot Logs",
            about="Xəta qeydləri burda saxlanılır ⚡",
            megagroup=True
        ))
        chat_id = result.chats[0].id
        with open(LOG_GROUP_FILE, "w") as f:
            f.write(str(chat_id))
    else:
        with open(LOG_GROUP_FILE) as f:
            chat_id = int(f.read().strip())

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(error_text)

    caption = (
        "**Ryhaven Userbot ⚡ #ΞЯ404**\n"
        "**Xəta baş verdi ❗**\n"
        "**ℹ️ Bu log'u** [dəstək gurupuna](https://t.me/RyhavenSupport) göndərin!"
    )

    try:
        await client.send_file(chat_id, LOG_FILE, caption=caption, link_preview=False)
    except:
        pass

# =================== START ===================
async def main():
    try:
        await client.start()
    except Exception as e:
        await send_log(str(e))
        return

    try:
        load_plugins()
    except Exception as e:
        await send_log(str(e))

    if os.path.exists(".restart_msg"):
        with open(".restart_msg") as f:
            chat_id, msg_id = f.read().split(":")
        try:
            await client.edit_message(int(chat_id), int(msg_id), " 🥷 Ryhaven Userbot Aktivdir")
        except:
            pass
        os.remove(".restart_msg")

    print("🥷 Ryhaven Userbot işə düşdü...")
    await client.run_until_disconnected()

asyncio.get_event_loop().run_until_complete(main())
