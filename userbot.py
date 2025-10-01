import os
import sys
import json
import traceback
import asyncio
import base64
import requests
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import CreateChannelRequest

# =================== CONFIG ===================
session_file = os.getenv("SESSION", "user.session")   # Session fayl adı
api_id = int(os.getenv("API_ID", "12345"))            # Telegram API_ID
api_hash = os.getenv("API_HASH", "")                  # Telegram API_HASH
client = TelegramClient(session_file, api_id, api_hash)

ADMIN_IDS = [8221469331]  # Admin ID (yalnız sənin üçün işləyəcək)
PLUGINS_FILE = "plugins.json"
ALIVE_FILE = "alive.json"
LOG_FILE = "error.log"
LOG_GROUP_FILE = f"{session_file}.loggroup"

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
        # İlk dəfə log qrupu yaradılır
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
    ).format(SUPPORT_GROUP)

    try:
        await client.send_file(chat_id, LOG_FILE, caption=caption, link_preview=False)
    except:
        pass


# =================== GITHUB HELPER ===================
def github_update_file(content, message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # əvvəlki faylı götür (sha lazımdır)
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
    if r.status_code in [200,201]:
        return True
    else:
        print("GitHub error:", r.text)
        return False


# =================== ƏSAS KOMANDALAR ===================
@client.on(events.NewMessage(pattern=r'\.alive'))
async def alive(event):
    alive_data = load_alive()
    msg = alive_data.get(str(event.sender_id), "Ryhaven Userbot Aktivdir ⚡")
    await event.edit(msg)


@client.on(events.NewMessage(pattern=r'\.dalive'))
async def dalive(event):
    args = event.raw_text.split(" ", 1)
    if len(args) == 1:
        return await event.edit("⚠️ İstifadə: `.dalive Mənim mesajım`")
    alive_data = load_alive()
    alive_data[str(event.sender_id)] = args[1]
    save_alive(alive_data)
    await event.edit("Alive mesajınız dəyişdirildi! Boss 🥷")


@client.on(events.NewMessage(pattern=r'\.valive'))
async def valive(event):
    if event.chat and event.chat.username != SUPPORT_GROUP:
        return
    await alive(event)


@client.on(events.NewMessage(pattern=r'\.vlive'))
async def vlive(event):
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


# =================== PLUGIN MANAGER ===================
@client.on(events.NewMessage(pattern=r'\.ek'))
async def ek(event):
    if event.sender_id not in ADMIN_IDS:
        return await event.edit("❌ Bu əmri yalnız admin istifadə edə bilər.")
    if not event.is_reply:
        return await event.edit("⚠️ `.ek` üçün reply edin.")
    replied = await event.get_reply_message()
    code_to_add = replied.message
    try:
        exec(code_to_add, globals())
        save_plugin(code_to_add)

        with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        if github_update_file(content, "Plugin əlavə edildi"):
            await event.edit("🚀 Plugin əlavə olundu və GitHub-a push edildi")
        else:
            await event.edit("⚠️ Plugin əlavə olundu amma GitHub-a push alınmadı")
    except Exception as e:
        error = traceback.format_exc()
        remove_plugin(code_to_add)
        await send_log(error)
        await event.edit("❌ Plugin xətalıdır, log göndərildi.")


@client.on(events.NewMessage(pattern=r'\.sil'))
async def sil(event):
    if event.sender_id not in ADMIN_IDS:
        return await event.edit("❌ Bu əmri yalnız admin istifadə edə bilər.")
    if not event.is_reply:
        return await event.edit("⚠️ `.sil` üçün reply edin.")
    replied = await event.get_reply_message()
    code_to_remove = replied.message
    try:
        remove_plugin(code_to_remove)

        with open(PLUGINS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        if github_update_file(content, "Plugin silindi"):
            await event.edit("🚮 Plugin silindi və GitHub-a push edildi")
        else:
            await event.edit("⚠️ Plugin silindi amma GitHub-a push alınmadı")
    except Exception as e:
        error = traceback.format_exc()
        await send_log(error)
        await event.edit("❌ Xəta baş verdi, log göndərildi.")


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