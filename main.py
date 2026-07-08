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

WELCOME_MESSAGE = """
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
    ("بی‌قانون‌آباد (جاوا و بدراک)", "mc.bigmc.ir"),
    ("ماین سیتی (جاوا)", "play.minecity.ir"),
    ("پرشیا کرفت (جاوا)", "play.persiacraft.ir"),
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
