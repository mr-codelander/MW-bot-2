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

# ------------------ START ------------------

@bot.on_message(filters.command("start"))
async def start(bot, message):
	if message.chat_id in ACTIVE_GROUPS:
        await message.reply(
        	"ربات فعاله!\n\nدستورات:\n/status <ip> : نمایش وضعیت سرور\n\nبرای تبلیغ سرور خود به این آیدی مراجعه کنید:\n@mr_war_aparat"
    	)
    else:
    	ACTIVE_GROUPS[message.chat_id] = True
    	save_active_groups(ACTIVE_GROUPS)
    	await message.reply()

@bot.on_message()
async def handler_ads(bot, message):
	if "/smaads " in message.text.lower():
            tads = text_lower.replace("/smaads ", "")
            for i in ACTIVE_GROUPS:
                await bot.send_message(chat_id=i, text=tads)
# ------------------ STATUS ------------------

import aiohttp

@bot.on_message(filters.command("status"))
async def status(bot, message):
    if not message.chat_id in ACTIVE_GROUPS:
    	return
    if not message.args:
        return await message.reply(
            "❌ استفاده:\n/status <ip>\nمثال:\n/status mc.hypixel.net"
        )

    ip = message.args[0]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.mcstatus.io/v2/status/java/{ip}",
                timeout=10
            ) as r:
                data = await r.json()

        if not data.get("online"):
            return await message.reply(
                f"🔴 سرور `{ip}` آفلاین است."
            )

        hostname = data.get("hostname", ip)

        motd = "ندارد"
        if data.get("motd"):
            clean = data["motd"].get("clean")
            if clean:
                motd = "\n".join(clean)

        players = data.get("players", {})
        version = data.get("version", {})
        software = data.get("software") or {}
        mapinfo = data.get("map") or {}
        mods = data.get("mods") or {}
        plugins = data.get("plugins") or {}

        online = players.get("online", 0)
        maximum = players.get("max", 0)

        player_list = "-"
        if players.get("list"):
            player_list = "\n".join("• "+x["name_clean"] for x in players["list"][:20])

        protocol = version.get("protocol", "-")
        version_name = version.get("name_clean", "-")

        latency = data.get("roundTripLatency", "-")

        brand = software.get("brand", "-")
        software_version = software.get("version", "-")

        text = f"""
🟢 Minecraft Server

🌍 IP
`{hostname}`

📡 Status
Online

📝 Description
{motd}

👥 Players
{online}/{maximum}

🎮 Version
{version_name}

🔢 Protocol
{protocol}

⚡ Ping
{latency} ms

🖥 Software
{brand}
{software_version}

🗺 Map
{mapinfo.get("clean_name","-")}

🧩 Plugins
{plugins.get("names","-")}

🛠 Mods
{mods.get("names","-")}

👤 Online Players
{player_list}
"""

        await message.reply(text)

    except Exception as e:
        await message.reply(f"❌ Error:\n{e}")

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
