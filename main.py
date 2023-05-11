import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, filters, CommandHandler, ContextTypes, MessageHandler
import requests
import urllib.request
import uuid
import base64


# 设置日志等级
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 获取API Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ImgBB API参数
params = {
    # 'expiration': '600',  # TODO: 引入文件一定时间后自动删除功能, 暂时为永久有效
    "key": os.getenv("IMGBB_API_KEY"),
}

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
    telegram_image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    file_name = f"./{str(uuid.uuid4())}{telegram_image_url[telegram_image_url.rfind('.'):]}"
    # 这里为了不向ImgBB暴露我们的Telegram Bot token, 先将文件下载到本地再上传
    urllib.request.urlretrieve(telegram_image_url, file_name)
    with open(file_name, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        # 上传文件到ImgBB
        files = {
            "image": (None, encoded_string),
        }

        response = requests.post('https://api.imgbb.com/1/upload', params=params, files=files)

        # 检查状态码
        if response.status_code != 200:
            await context.bot.send_message(chat_id=chat_id, text="抱歉, 处理失败, " + str(response.text))
            return

        data = response.json()
        imgbb_image_url = data["data"]["image"]["url"]

        # 发送图片直链给用户
        await context.bot.send_message(chat_id=chat_id, text=imgbb_image_url)
        
    # 删除文件
    os.remove(f"./{file_name}")
   

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
