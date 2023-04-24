import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, filters, CommandHandler, ContextTypes, MessageHandler
import requests


# 设置日志等级
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 获取API Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 定义消息处理函数，接收图片并发送到Telegram Bot
async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    photo_file = update.message.document.file_id
    print(photo_file)

    # 向Telegram Bot发送图片
    # await context.bot.send_photo(chat_id=chat_id, photo=photo_file)
    # 向Telegram Bot API请求获取图片直链
    r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={photo_file}")
    # 解析返回的JSON数据，获取图片直链
    file_path = r.json()['result']['file_path']
    image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    # 发送图片直链给用户
    await context.bot.send_message(chat_id=chat_id, text=image_url)

# 定义错误处理函数
def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.warning(f"Update {update} caused error {context.error}")

# 定义命令处理函数，回复Bot的信息
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id, text="欢迎使用图片上传Bot！请发送一张图片。")

# 定义命令处理函数，回复Bot的信息
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.message.chat_id, text="请发送一张图片，我会返回图片的直链。")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    message_handler = MessageHandler(filters.Document.IMAGE, send_image)
    
    application.add_handler(message_handler)
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_error_handler(error)
    
    application.run_polling()