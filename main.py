import os
import threading
import requests
from PIL import Image
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")

bot = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

app = Flask(__name__)
@app.route("/")
def home():
    return "✅ Bot is alive!"

def start_web():
    app.run(host="0.0.0.0", port=10000)

def process_image(photo_path):
    with open(photo_path, "rb") as image_file:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": image_file},
            data={"size": "auto"},
            headers={"X-Api-Key": REMOVE_BG_API_KEY},
        )

    if response.status_code != 200:
        return None

    result = Image.open(BytesIO(response.content)).convert("RGBA")
    result = result.resize((512, 512), Image.LANCZOS)
    result_path = "sticker.png"
    result.save(result_path)
    return result_path

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply("👋 Send me a photo and I’ll turn it into a sticker-ready image (background removed).")

@bot.on_message(filters.photo & filters.private)
async def photo(_, message: Message):
    msg = await message.reply("⏳ Processing...")
    file_path = await message.download()
    final_path = process_image(file_path)

    if final_path:
        await message.reply_photo(
            photo=final_path,
            caption="✅ Sticker ready!\nSend this image to [@Stickers](https://t.me/Stickers) to add it to your pack."
        )
    else:
        await message.reply("❌ Failed to remove background.")
    
    await msg.delete()
    os.remove(file_path)
    if final_path: os.remove(final_path)

if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    bot.run()
