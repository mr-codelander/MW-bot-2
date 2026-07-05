import asyncio
from rubka import Robot, filters

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
import aiohttp
from mcstatus import JavaServer

class MinecraftStatus:

    def __init__(self):
        self.timeout = 5
        self.session = None

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def status(self, address):
        methods = [
            self.mcstatus_method,
            self.mcstatusio,
            self.mcsrvstat,
            self.mcsrvstat_v3,
            self.direct_socket
        ]

        last_error = None

        for method in methods:
            try:
                result = await method(address)
                if result and result.get("online"):
                    return result
            except Exception as e:
                last_error = e

        return {
            "online": False,
            "error": str(last_error) if last_error else "Unknown"
        }

    async def mcstatus_method(self, address):

        if ":" in address:
            server = JavaServer.lookup(address)
        else:
            server = JavaServer.lookup(f"{address}:25565")

        status = await server.async_status()

        players = []

        if status.players.sample:
            players = [p.name for p in status.players.sample]

        motd = status.description

        if isinstance(motd, dict):
            motd = motd.get("text", "")

        elif isinstance(motd, list):
            motd = "".join(map(str, motd))

        return {
            "online": True,
            "ip": address,
            "motd": str(motd),
            "version": status.version.name,
            "online_players": status.players.online,
            "max_players": status.players.max,
            "ping": round(status.latency,1)
        }

    async def mcstatusio(self,address):

        session = await self.get_session()

        async with session.get(
            f"https://api.mcstatus.io/v2/status/java/{address}"
        ) as r:

            if r.status != 200:
                raise Exception("HTTP")

            data = await r.json()

        if not data.get("online"):
            raise Exception("Offline")

        motd=""

        clean=data.get("motd",{}).get("clean","")

        if isinstance(clean,list):
            if clean and all(len(str(i))==1 for i in clean):
                motd="".join(clean)
            else:
                motd="\n".join(clean)
        else:
            motd=str(clean)

        players=[]

        plist=data.get("players",{}).get("list",[])

        for p in plist:
            if isinstance(p,dict):
                players.append(p.get("name",""))
            else:
                players.append(str(p))

        return{
            "online":True,
            "ip":address,
            "motd":motd,
            "version":data.get("version",{}).get("name","-"),
            "online_players":data.get("players",{}).get("online",0),
            "max_players":data.get("players",{}).get("max",0),
            "ping":data.get("debug",{}).get("ping","-")
		}
    async def mcsrvstat(self, address):

        session = await self.get_session()

        async with session.get(
            f"https://api.mcsrvstat.us/3/{address}"
        ) as r:

            if r.status != 200:
                raise Exception("HTTP")

            data = await r.json()

        if not data.get("online"):
            raise Exception("Offline")

        players = []

        if data.get("players") and data["players"].get("list"):
            for p in data["players"]["list"]:
                players.append(str(p))

        motd = ""

        if data.get("motd"):
            motd = "\n".join(data["motd"].get("clean", []))

        return {
            "online": True,
            "ip": address,
            "motd": motd,
            "version": data.get("version", "-"),
            "online_players": data.get("players", {}).get("online", 0),
            "max_players": data.get("players", {}).get("max", 0),
            "ping": "-"
        }


    async def mcsrvstat_v3(self, address):

        session = await self.get_session()

        async with session.get(
            f"https://api.mcsrvstat.us/2/{address}"
        ) as r:

            if r.status != 200:
                raise Exception("HTTP")

            data = await r.json()

        if not data.get("online"):
            raise Exception("Offline")

        motd = ""

        if data.get("motd"):

            if isinstance(data["motd"], list):
                motd = "\n".join(data["motd"])
            else:
                motd = str(data["motd"])

        return {
            "online": True,
            "ip": address,
            "motd": motd,
            "version": data.get("version", "-"),
            "online_players": data.get("players", {}).get("online", 0),
            "max_players": data.get("players", {}).get("max", 0),
            "ping": "-"
        }


    async def direct_socket(self, address):

        if ":" in address:
            host, port = address.split(":")
            port = int(port)
        else:
            host = address
            port = 25565

        loop = asyncio.get_running_loop()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=3
            )

            writer.close()

            try:
                await writer.wait_closed()
            except:
                pass

            return {
                "online": True,
                "ip": address,
                "motd": "",
                "version": "-",
                "online_players": 0,
                "max_players": 0,
                "ping": "-"
            }

        except Exception:
            raise Exception("Socket connection failed")
# ------------------ START ------------------

@bot.on_message(commands=["start"])
async def start(bot, message):
	if message.chat_id in ACTIVE_GROUPS:
		return await message.reply("ربات فعاله!\n\nدستورات:\n/status <ip> : نمایش وضعیت سرور\n\nبرای تبلیغ سرور خود به این آیدی مراجعه کنید:\n@mr_war_aparat")
	else:
		ACTIVE_GROUPS[message.chat_id] = True
		return await message.reply(WELCOME_MESSAGE)
		save_active_groups(ACTIVE_GROUPS)

@bot.on_message()
async def handler_ads(bot, message):
	if "/smaads " in message.text.lower():
            tads = text_lower.replace("/smaads ", "")
            for i in ACTIVE_GROUPS:
                await bot.send_message(chat_id=i, text=tads)
# ------------------ STATUS ------------------
status_checker = MinecraftStatus()


@bot.on_message(commands=["status"])
async def status(bot, message):

    if message.chat_id not in ACTIVE_GROUPS:
        return

    if not message.args:
        return await message.reply(
            "❌ استفاده:\n/status <ip>\nمثال:\n/status mc.hypixel.net"
        )

    address = message.args[0]

    msg = await message.reply("🔍 درحال بررسی سرور...\nمنتظر بمون!")

    try:

        info = await status_checker.status(address)

        if not info["online"]:
            return await msg.edit(
                f"""🔴 Server Offline

🌍 IP
`{address}`

❌ Error

{info.get("error","Unknown")}
"""
            )

        text = f"""🟢 Minecraft Server

🌍 IP
`{info['ip']}`

📡 Status
Online

📝 Description
{motd}

👥 Players
{info['online_players']}/{info['max_players']}

🎮 Version
{info['version']}

⚡ Ping
{info['ping']} ms
"""

        await msg.edit(text)

    except Exception as e:

        await msg.edit(
            f"""🔴 Server Offline

🌍 IP
`{address}`

❌ Error

`{e}`
"""
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
