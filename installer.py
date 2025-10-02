import os
import sys
import json
import traceback
import asyncio
import base64
import requests
from telethon import events
from telethon import TelegramClient, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import CreateChannelRequest

# =================== CONFIG ===================
api_id = int(os.getenv("API_ID", "12345"))            # Telegram API_ID
api_hash = os.getenv("API_HASH", "")                  # Telegram API_HASH
session_string = os.getenv("RSESSION")                # StringSession (SQLite YOX!)

client = TelegramClient(StringSession(session_string), api_id, api_hash)

ADMIN_IDS = [8221469331]  # Admin ID
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


# =================== AUTO BOLD ===================
@client.on(events.NewMessage(outgoing=True))
async def auto_bold_outgoing(event):
    if event.text and not (event.text.startswith("**") and event.text.endswith("**")):
        try:
            await event.edit(f"**{event.text}**")
        except:
            pass

# Custom wrapper: bold reply & respond
async def bold_reply(event, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = (f"**{args[0]}**",) + args[1:]
    return await event.__class__.reply(event, *args, **kwargs)

async def bold_respond(event, *args, **kwargs):
    if args and isinstance(args[0], str):
        args = (f"**{args[0]}**",) + args[1:]
    return await event.__class__.respond(event, *args, **kwargs)

# Monkeypatch etmək əvəzinə helper funksiyalar
def patch_event(event):
    event.bold_reply = lambda *a, **k: bold_reply(event, *a, **k)
    event.bold_respond = lambda *a, **k: bold_respond(event, *a, **k)
    return event

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
        f"**ℹ️ Bu log'u** [dəstək qrupuna](https://t.me/{SUPPORT_GROUP}) göndərin!"
    )

    try:
        await client.send_file(chat_id, LOG_FILE, caption=caption, link_preview=False)
    except:
        pass

# =================== GITHUB HELPER ===================
def github_update_file(content, message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    resp = requests.get(url, headers=headers)
    sha = None
    if resp.status_code == 200:
        sha = resp.json()["sha"]

    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    if r.status_code in [200, 201]:
        return True
    else:
        print("GitHub error:", r.text)
        return False

# =================== ƏSAS KOMANDALAR ===================
@client.on(events.NewMessage(pattern=r'\.alive'))
async def alive(event):
    event = patch_event(event)
    alive_data = load_alive()
    msg = alive_data.get(str(event.sender_id), "Ryhaven Userbot Aktivdir ⚡")
    await event.edit(f"**{msg}**")

@client.on(events.NewMessage(pattern=r'\.dalive'))
async def dalive(event):
    event = patch_event(event)
    args = event.raw_text.split(" ", 1)
    if len(args) == 1:
        return await event.edit("⚠️ İstifadə: `.dalive Mənim mesajım`")
    alive_data = load_alive()
    alive_data[str(event.sender_id)] = args[1]
    save_alive(alive_data)
    await event.edit("Alive mesajınız dəyişdirildi! Boss 🥷")

@client.on(events.NewMessage(pattern=r'\.vlive'))
async def vlive(event):
    event = patch_event(event)
    sender = await event.get_sender()
    if sender.id not in ADMIN_IDS:
        return await event.edit("❌ Bu əmri yalnız admin istifadə edə bilər.")
    await event.respond("Ryhaven Userbot Aktivdir! Boss 🥷")

@client.on(events.NewMessage(pattern=r'\.restart'))
async def restart(event):
    msg = await event.edit("♻️ Ryhaven Userbot yenidən başlayır...")
    with open(".restart_msg", "w") as f:
        f.write(str(event.chat_id) + ":" + str(msg.id))
    os.execv(sys.executable, ['python'] + sys.argv)

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
            await client.edit_message(int(chat_id), int(msg_id), "🥷 Ryhaven Userbot Aktivdir")
        except:
            pass
        os.remove(".restart_msg")

    print("🥷 Ryhaven Userbot işə düşdü...")
    await client.run_until_disconnected()

asyncio.get_event_loop().run_until_complete(main())
