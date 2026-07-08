# ==========================================
# Import ها
# ==========================================
import socket
import asyncio
import requests

from rubka import Bot
from rubka.filters import Filters
from rubka.keypad import ChatKeypadBuilder
# ==========================================
# متن خوشامد
# ==========================================

A_MESSAGE = """
🥳 ربات فعاله !
از منوی زیر گزینه موردنظر خود را انتخاب کنید:
"""
# ==========================================
# لیست سرورهای معروف
# ==========================================

SERVERS = [
    ("هایپیکسل (جاوا)", "mc.hypixel.net"),
    ("کیوب‌کرفت (جاوا و بدراک)", "play.cubecraft.net"),
    ("ام‌سی‌سی آیلند (جاوا)", "play.mccisland.net"),
    ("گیم آپ (جاوا)", "mc.gameup.ir"),
    ("تیرکس ماین (جاوا)", "play.trexmine.com"),
    ("اپکس ماین (بدراک)", "play.apexgaming.ir"),
    ("گان مکس (جاوا)", "play.gunmax.org"),
    ("بی‌قانون‌آباد (جاوا و بدراک)", "mc.bigmc.ir")
]
TOKEN = "BIHJFI0MEOTMVGGAXRABWENZHWJGBQDPLVWMTRMLPIYWBPMRBLTTXPKQZYHHUVVJ"

bot = Robot(
    token=TOKEN,
    parse_mode="Markdown",
    api_endpoint="botapi"
)
import psycopg2
import os

db_url = os.getenv("DATABASE_URL")
print(repr(db_url))

conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS ACTIVE_GROUPS (
    guid TEXT PRIMARY KEY
)
""")
conn.commit()
def save_active_groups(ACTIVE_GROUPS):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ACTIVE_GROUPS (
            guid TEXT PRIMARY KEY,
            active BOOLEAN NOT NULL
        )
    """)

    cur.execute("DELETE FROM ACTIVE_GROUPS")

    for guid, active in ACTIVE_GROUPS.items():
        cur.execute(
            "INSERT INTO ACTIVE_GROUPS (guid, active) VALUES (%s, %s)",
            (guid, active)
        )

    conn.commit()


def load_active_groups():
    cur.execute("SELECT guid, active FROM ACTIVE_GROUPS")
    rows = cur.fetchall()

    return {guid: active for guid, active in rows}
# ========== متغیرهای سراسری ==========
try:
    ACTIVE_GROUPS = load_active_groups()
except:
    ACTIVE_GROUPS = {}
WELCOME_MESSAGE = """سلام! 👋
به ربات سرور های ماینکرفت خوش آمدید
اگر در کانال زیر عضو نیستید ،
📢 @mr_bwars
عضو شوید
و بعد مجدد /start را بزنید ❤️"""
import socket
import time
import requests
import dns.resolver

from mcstatus import JavaServer


class MinecraftStatus:

    CACHE = {}
    CACHE_TIME = 30

    # -----------------------------
    # Cache
    # -----------------------------

    @classmethod
    def get_cache(cls, key):
        if key not in cls.CACHE:
            return None

        data, created = cls.CACHE[key]

        if time.time() - created > cls.CACHE_TIME:
            del cls.CACHE[key]
            return None

        return data

    @classmethod
    def set_cache(cls, key, value):
        cls.CACHE[key] = (
            value,
            time.time()
        )

    # -----------------------------
    # DNS
    # -----------------------------

    @staticmethod
    def resolve(host):

        try:
            return socket.gethostbyname(host)
        except:
            return None

    @staticmethod
    def srv(host):

        try:

            answers = dns.resolver.resolve(
                "_minecraft._tcp." + host,
                "SRV"
            )

            record = answers[0]

            return {
                "host": str(record.target).rstrip("."),
                "port": int(record.port)
            }

        except:
            return None

    # -----------------------------
    # Java
    # -----------------------------

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

        except Exception:

            return None

    # -----------------------------
    # API
    # -----------------------------

    @staticmethod
    def request(url):

        try:

            return requests.get(
                url,
                timeout=4
            ).json()

        except:

            return None

    # -----------------------------
    # Result
    # -----------------------------

    @staticmethod
    def offline(host):

        return {

            "success": False,

            "host": host,

            "edition": None,

            "online": False,

            "reason": "سرور پیدا نشد."

        }
	# -----------------------------
    # API : mcsrvstat.us
    # -----------------------------

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

    # -----------------------------
    # API : mcstatus.io (Java)
    # -----------------------------

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

    # -----------------------------
    # API : mcstatus.io (Bedrock)
    # -----------------------------

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

    # -----------------------------
    # Auto Detect
    # -----------------------------

    @classmethod
    def detect(cls, host):

        cache = cls.get_cache(host)

        if cache:
            return cache

        srv = cls.srv(host)

        if srv:

            java = cls.java(
                srv["host"],
                srv["port"]
            )

            if java:
                cls.set_cache(host, java)
                return java

        java = cls.java(host)

        if java:
            cls.set_cache(host, java)
            return java

        result = cls.api_mcstatus_java(host)

        if result:
            cls.set_cache(host, result)
            return result

        result = cls.api_mcstatus_bedrock(host)

        if result:
            cls.set_cache(host, result)
            return result

        result = cls.api_mcsrvstat(host)

        if result:
            cls.set_cache(host, result)
            return result

        return cls.offline(host)
	# -----------------------------
    # Retry
    # -----------------------------

    @classmethod
    def check(cls, host):

        host = host.strip()

        if host.startswith("minecraft://"):
            host = host.replace("minecraft://", "")

        if host.startswith("mc://"):
            host = host.replace("mc://", "")

        if host.startswith("https://"):
            host = host.replace("https://", "")

        if host.startswith("http://"):
            host = host.replace("http://", "")

        host = host.split("/")[0]

        if ":" in host:
            host, port = host.split(":", 1)

            try:
                port = int(port)

                java = cls.java(host, port)

                if java:
                    cls.set_cache(f"{host}:{port}", java)
                    return java

            except:
                pass

        for _ in range(2):

            try:

                result = cls.detect(host)

                if result and result.get("success"):
                    return result

            except:
                pass

            time.sleep(0.4)

        return cls.offline(host)

    # -----------------------------
    # Pretty Text
    # -----------------------------

    @staticmethod
    def format(data):

        if not data["success"]:

            return (
                "❌ سرور آفلاین است.\n\n"
                f"🌐 آدرس: {data['host']}"
            )

        edition = {
            "Java": "☕ جاوا",
            "Bedrock": "🪨 بدراک"
        }.get(data["edition"], data["edition"])

        text = (
            "🟢 سرور آنلاین است\n\n"
            f"🌐 آدرس: {data['host']}\n"
            f"🎮 نسخه: {edition}\n"
            f"📦 ورژن: {data['version']}\n"
            f"👥 بازیکنان: {data['players_online']}/{data['players_max']}"
        )

        if data.get("latency"):
            text += f"\n⚡ پینگ: {data['latency']} ms"

        if data.get("motd"):
            text += f"\n\n📜 MOTD:\n{data['motd']}"

        return text

    # -----------------------------
    # Quick Status
    # -----------------------------

    @classmethod
    def status(cls, host):

        result = cls.check(host)

        return cls.format(result)


    @classmethod
    def list_servers(cls):

        result = []

        for name, ip in cls.SERVERS:

            status = cls.check(ip)

            if status["success"]:

                players = (
                    f"{status['players_online']}/"
                    f"{status['players_max']}"
                )

            else:

                players = "آفلاین"

            result.append({
                "name": name,
                "ip": ip,
                "players": players
            })

        return result
# ------------------ START ------------------

@bot.on_message(commands=["start"])
async def start(bot, message):
	if message.chat_id in ACTIVE_GROUPS:
		keypad = (
            ChatKeypadBuilder()

            .row(
                ChatKeypadBuilder.button_simple(
                    id="servers",
                    text="🌍 سرورهای ماینکرفت"
                ),
                ChatKeypadBuilder.button_textbox(
                    id="status",
                    text="🔍 استعلام سرور"
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
		return
	else:
		ACTIVE_GROUPS[message.chat_id] = True
		await message.reply(WELCOME_MESSAGE)
		save_active_groups(ACTIVE_GROUPS)
		return

@bot.on_message()
async def handler_ads(bot, message):
	if "/smaads " in message.text.lower():
            tads = text_lower.replace("/smaads ", "")
            for i in ACTIVE_GROUPS:
                await bot.send_message(chat_id=i, text=tads)
#استاتوس
@bot.on_message(filters=lambda m: m.button_id == "server_ip")
def get_status(bot, message):

    ip = message.data
	msg = message.reply("🔎 در حال بررسی سرور...")
    result = MinecraftStatus.status(ip)

    msg.edit(result)
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
