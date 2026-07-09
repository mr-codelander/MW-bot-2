# ==========================================
# Import ها
# ==========================================

import os
import time
import socket
import asyncio
import requests
import psycopg2
import dns.resolver

from mcstatus import JavaServer

from rubka import Robot
from rubka.keypad import ChatKeypadBuilder


# ==========================================
# تنظیمات
# ==========================================

TOKEN = "BIHJFI0MEOTMVGGAXRABWENZHWJGBQDPLVWMTRMLPIYWBPMRBLTTXPKQZYHHUVVJ"

bot = Robot(
    token=TOKEN,
    parse_mode="Markdown",
    api_endpoint="botapi"
)


# ==========================================
# دیتابیس
# ==========================================

db_url = os.getenv("DATABASE_URL")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS ACTIVE_GROUPS(
    guid TEXT PRIMARY KEY,
    active BOOLEAN NOT NULL
)
""")

conn.commit()


# ==========================================
# متن ها
# ==========================================

A_MESSAGE = """
🥳 ربات فعاله!

از منوی زیر گزینه موردنظر خود را انتخاب کنید.
"""

WELCOME_MESSAGE = """
سلام 👋

به ربات استعلام سرورهای ماینکرفت خوش آمدید.
"""


# ==========================================
# لیست سرورها
# ==========================================

SERVERS = [

    ("هایپیکسل (جاوا)", "mc.hypixel.net"),

    ("کیوب کرافت (جاوا و بدراک)", "play.cubecraft.net"),

    ("ام سی سی آیلند (جاوا)", "play.mccisland.net"),

    ("گیم آپ (جاوا)", "mc.gameup.ir"),

    ("تیرکس ماین (جاوا)", "play.trexmine.com"),

    ("اپکس ماین (بدراک)", "play.apexgaming.ir"),

    ("گان مکس (جاوا)", "play.gunmax.org"),

    ("بی قانون آباد (جاوا و بدراک)", "mc.bigmc.ir"),

    ("وان بلاک (جاوا)", "play.oneblockmc.com"),

    ("جارتکس (جاوا)", "jartex.fun")
]


# ==========================================
# دیتابیس گروه ها
# ==========================================

def save_active_groups(data):

    cur.execute("DELETE FROM ACTIVE_GROUPS")

    for guid, active in data.items():

        cur.execute(
            "INSERT INTO ACTIVE_GROUPS(guid,active) VALUES(%s,%s)",
            (guid, active)
        )

    conn.commit()


def load_active_groups():

    cur.execute(
        "SELECT guid,active FROM ACTIVE_GROUPS"
    )

    rows = cur.fetchall()

    return {
        guid: active
        for guid, active in rows
    }


try:

    ACTIVE_GROUPS = load_active_groups()

except:

    ACTIVE_GROUPS = {}


# ==========================================
# کلاس استعلام
# ==========================================

class MinecraftStatus:

    CACHE = {}

    CACHE_TIME = 30

    SERVERS = SERVERS

    @classmethod
    def get_cache(cls, key):

        item = cls.CACHE.get(key)

        if not item:
            return None

        value, created = item

        if time.time() - created > cls.CACHE_TIME:

            del cls.CACHE[key]

            return None

        return value

    @classmethod
    def set_cache(cls, key, value):

        cls.CACHE[key] = (
            value,
            time.time()
        )

    @staticmethod
    def request(url):

        try:

            return requests.get(
                url,
                timeout=5
            ).json()

        except:

            return None

    @staticmethod
    def resolve(host):

        try:

            return socket.gethostbyname(host)
        except:
            return None

    @staticmethod
    def srv(host):
        try:
            answer = dns.resolver.resolve(
                "_minecraft._tcp." + host,
                "SRV"
            )[0]
            return {
                "host": str(answer.target).rstrip("."),
                "port": int(answer.port)
            }
        except:
            return None

    @staticmethod
    def java(host, port=25565):
        try:
            server = JavaServer.lookup(
                f"{host}:{port}"
            )
            status = server.status()
            return {
                "success": True,
                "edition": "Java",
                "host": host,
                "port": port,
                "version": status.version.name,
                "players_online": status.players.online,
                "players_max": status.players.max,
                "latency": round(status.latency),
                "motd": str(status.description),
                "icon": status.icon
            }
        except:
            return None
    @classmethod
    def api_mcsrvstat(cls, host):
        data = cls.request(
            f"https://api.mcsrvstat.us/3/{host}"
        )
        if not data:
            return None
        if not data.get("online"):
            return None
        players = data.get("players", {})

        return {
            "success": True,
            "online": True,
            "edition": "Java",
            "host": data.get("hostname", host),
            "port": data.get("port", 25565),
            "version": data.get("version"),
            "players_online": players.get("online", 0),
            "players_max": players.get("max", 0),
            "motd": "\n".join(
                data.get("motd", {}).get("clean", [])
            ),
            "icon": data.get("icon")
        }

    @classmethod
    def api_mcstatus_java(cls, host):

        data = cls.request(
            f"https://api.mcstatus.io/v2/status/java/{host}"
        )

        if not data:
            return None

        if not data.get("online"):
            return None

        players = data.get("players", {})
        version = data.get("version", {})
        motd = data.get("motd", {})

        return {
            "success": True,
            "online": True,
            "edition": "Java",
            "host": host,
            "port": data.get("port", 25565),
            "version": version.get("name_clean"),
            "players_online": players.get("online", 0),
            "players_max": players.get("max", 0),
            "motd": "\n".join(
                motd.get("clean", [])
            ),
            "icon": data.get("icon")
        }

    @classmethod
    def api_mcstatus_bedrock(cls, host):

        data = cls.request(
            f"https://api.mcstatus.io/v2/status/bedrock/{host}"
        )

        if not data:
            return None

        if not data.get("online"):
            return None

        players = data.get("players", {})
        version = data.get("version", {})
        motd = data.get("motd", {})

        return {
            "success": True,
            "online": True,
            "edition": "Bedrock",
            "host": host,
            "port": data.get("port", 19132),
            "version": version.get("name"),
            "players_online": players.get("online", 0),
            "players_max": players.get("max", 0),
            "motd": "\n".join(
                motd.get("clean", [])
            ),
            "icon": None
        }

    @classmethod
    def detect(cls, host):

        cache = cls.get_cache(host)

        if cache:
            return cache

        srv = cls.srv(host)

        if srv:

            result = cls.java(
                srv["host"],
                srv["port"]
            )

            if result:
                cls.set_cache(host, result)
                return result

        result = cls.java(host)

        if result:
            cls.set_cache(host, result)
            return result

        for func in (
            cls.api_mcstatus_java,
            cls.api_mcstatus_bedrock,
            cls.api_mcsrvstat
        ):

            try:

                result = func(host)

                if result:

                    cls.set_cache(host, result)

                    return result

            except:
                pass

        return {
            "success": False,
            "host": host,
            "online": False
        }

    @classmethod
    def check(cls, host):

        host = (
            host.replace("https://", "")
            .replace("http://", "")
            .replace("minecraft://", "")
            .replace("mc://", "")
            .split("/")[0]
            .strip()
        )

        if ":" in host:

            ip, port = host.split(":", 1)

            try:

                result = cls.java(
                    ip,
                    int(port)
                )

                if result:
                    return result

            except:
                pass

        for _ in range(2):

            result = cls.detect(host)

            if result.get("success"):
                return result

            time.sleep(0.4)

        return {
            "success": False,
            "host": host,
            "online": False
		}
    @classmethod
    def format_status(cls, data):

        if not data.get("success"):

            return (
                "🔴 سرور آفلاین است.\n\n"
                f"🌐 آدرس: `{data['host']}`"
            )

        edition = data.get("edition", "Unknown")
        version = data.get("version", "Unknown")
        online = data.get("players_online", 0)
        maximum = data.get("players_max", 0)
        latency = data.get("latency", "-")
        motd = data.get("motd") or "ندارد"

        return f"""🟢 سرور آنلاین است

🌐 آدرس: `{data['host']}`
🎮 نسخه: {edition}
📦 ورژن: {version}
👥 بازیکنان: {online}/{maximum}
📡 پینگ: {latency}

📜 MOTD:
{motd}
"""

    @classmethod
    def all_servers(cls):

        text = "📋 لیست سرورهای ماینکرفت\n\n"

        for name, host in cls.SERVERS:

            try:

                result = cls.check(host)

                if result["success"]:

                    emoji = "🟢"

                    players = (
                        f"{result['players_online']}/"
                        f"{result['players_max']}"
                    )

                else:

                    emoji = "🔴"
                    players = "Offline"

            except:

                emoji = "⚪"
                players = "Unknown"

            text += (
                f"{emoji} {name}\n"
                f"🌐 `{host}`\n"
                f"👥 {players}\n\n"
            )

        return text

    @classmethod
    def server_names(cls):

        return [
            name
            for name, host in cls.SERVERS
        ]

    @classmethod
    def server_host(cls, name):

        for server_name, host in cls.SERVERS:

            if server_name == name:

                return host

        return None

    @classmethod
    def refresh_cache(cls):

        cls.CACHE.clear()

    @classmethod
    def preload(cls):

        for _, host in cls.SERVERS:

            try:

                cls.detect(host)

            except:

                pass


minecraft = MinecraftStatus()

# ======== پایان کلاس ========
# ------------------ START ------------------

@bot.on_message(commands=["start"])
async def start(bot, message):

    if message.chat_id not in ACTIVE_GROUPS:

        ACTIVE_GROUPS[message.chat_id] = True
        save_active_groups(ACTIVE_GROUPS)

    keypad = (
        ChatKeypadBuilder()

        .row(
            ChatKeypadBuilder.button_simple(
                id="servers",
                text="🌍 سرورهای ماینکرفت"
            ),
            ChatKeypadBuilder.button_textbox(
                id="status",
                title="🔍 استعلام سرور",
                type_line="SingleLine",
                type_keypad="String",
                place_holder="mc.hypixel.net"
            )
        )

        .row(
            ChatKeypadBuilder.button_simple(
                id="ads",
                text="📢 تبلیغات"
            ),
            ChatKeypadBuilder.button_simple(
                id="about",
                text="ℹ️ درباره ما"
            )
        )

        .build()
    )

    await message.reply_keypad(
        text=A_MESSAGE,
        keypad=keypad
    )


# ------------------ لیست سرورها ------------------

@bot.on_message(filters=lambda m: m.button_id == "servers")
async def servers(bot, message):

    text = "🌍 لیست سرورهای ماینکرفت\n\n"

    for name, ip in SERVERS:

        try:

            status = MinecraftStatus.check(ip)

            if status["success"]:
                online = (
                    f"{status['players_online']}/"
                    f"{status['players_max']}"
                )
                emoji = "🟢"

            else:
                online = "آفلاین"
                emoji = "🔴"

        except:
            emoji = "⚪"
            online = "خطا"

        text += (
            f"{emoji} {name}\n"
            f"🌐 `{ip}`\n"
            f"👥 {online}\n\n"
        )

    await message.reply(text)


# ------------------ استعلام ------------------

@bot.on_message(filters=lambda m: m.button_id == "status")
async def status(bot, message):

    ip = message.data.strip()

    wait = await message.reply(
        "⏳ درحال بررسی سرور..."
    )

    result = MinecraftStatus.check(ip)
    await wait.edit(
        MinecraftStatus.format_status(result)
    )

# ------------------ تبلیغات ------------------
@bot.on_message()
async def handler_ads(bot, message):

    if not message.is_text:
        return

    tl = message.text.lower()

    if tl.startswith("/smaads "):

        ad = message.text[8:].strip()

        for c in ACTIVE_GROUPS:

            try:
                await bot.send_message(
                    chat_id=c,
                    text=ad
                )
            except Exception:
                pass

        return

    elif tl == "📢 تبلیغات":

        await message.reply(
            "برای تبلیغ سرور خود می‌توانید به آیدی زیر مراجعه کنید:\n@Mr_war_aparat"
        )

        return
# ------------------ درباره ------------------

@bot.on_message(filters=lambda m: m.button_id == "about")
async def about(bot, message):

    await message.reply(
        "ℹ️ ربات استعلام سرورهای ماینکرفت\n\n"
        "نسخه 2.0"
    )


# ------------------ MAIN ------------------

async def main():

    await bot._initialize_webhook()
    await bot.geteToken()

    print("Connecting to the server...")
    print("Bot started successfully")

    while True:

        try:

            updates = await bot._fetch_updates(100)

            for update in updates:

                try:
                    await bot._process_update(update)
                except Exception as e:
                    print("Handler Error:", e)

            await asyncio.sleep(0.05)

        except Exception as e:

            print("Main Loop Error:", e)
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
