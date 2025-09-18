import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext import filters # <--- اضافه کردن این خط
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import platform
import psutil
import subprocess
import re
import datetime # <--- اضافه کردن این خط برای datetime.datetime

# توکن ربات خود را اینجا قرار دهید
TOKEN = 'YOUR_BOT_TOKEN'

# تابع برای شروع ربات و نمایش دکمه‌ها
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("پینگ IP/هاست", callback_data='ping')],
        [InlineKeyboardButton("اطلاعات سرور", callback_data='server_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('به ربات خوش آمدید! یکی از گزینه‌های زیر را انتخاب کنید:', reply_markup=reply_markup)

# تابع برای مدیریت کلیک دکمه‌ها
def button(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'ping':
        # برای edit_message_text باید یک message_id داشته باشید.
        # اگر می خواهید پیام جدیدی ارسال شود، از reply_text استفاده کنید.
        # اگر می خواهید پیام دکمه را ویرایش کنید:
        query.edit_message_text(text="لطفاً IP آدرس یا نام هاست مورد نظر را برای پینگ وارد کنید:")
        context.user_data['state'] = 'awaiting_ping_target'
    elif query.data == 'server_info':
        send_server_info(query, context)

# تابع برای ارسال اطلاعات سرور
def send_server_info(update_obj, context):
    # آپتایم سرور
    uptime_seconds = psutil.boot_time()
    uptime_str = get_uptime_string(uptime_seconds)

    # استفاده از CPU
    cpu_percent = psutil.cpu_percent(interval=1)

    # استفاده از RAM
    ram = psutil.virtual_memory()
    ram_total = f"{ram.total / (1024**3):.2f} GB"
    ram_used = f"{ram.used / (1024**3):.2f} GB ({ram.percent}%)"
    ram_free = f"{ram.free / (1024**3):.2f} GB"

    # اطلاعات شبکه (مثال - می‌توانید جزئیات بیشتری اضافه کنید)
    net_io = psutil.net_io_counters()
    bytes_sent = f"{net_io.bytes_sent / (1024**2):.2f} MB"
    bytes_recv = f"{net_io.bytes_recv / (1024**2):.2f} MB"

    info_message = (
        f"<b>اطلاعات سرور:</b>\n\n"
        f"<b>آپتایم:</b> {uptime_str}\n"
        f"<b>استفاده از CPU:</b> {cpu_percent}%\n"
        f"<b>RAM کل:</b> {ram_total}\n"
        f"<b>RAM استفاده شده:</b> {ram_used}\n"
        f"<b>RAM آزاد:</b> {ram_free}\n"
        f"<b>داده ارسال شده (شبکه):</b> {bytes_sent}\n"
        f"<b>داده دریافت شده (شبکه):</b> {bytes_recv}\n"
    )
    update_obj.edit_message_text(text=info_message, parse_mode='HTML')

def get_uptime_string(boot_time_seconds):
    # import datetime از بالای فایل منتقل شد
    boot_time = datetime.datetime.fromtimestamp(boot_time_seconds)
    current_time = datetime.datetime.now()
    uptime_delta = current_time - boot_time

    days = uptime_delta.days
    hours = uptime_delta.seconds // 3600
    minutes = (uptime_delta.seconds % 3600) // 60
    seconds = uptime_delta.seconds % 60

    uptime_str = ""
    if days > 0:
        uptime_str += f"{days} روز و "
    if hours > 0:
        uptime_str += f"{hours} ساعت و "
    if minutes > 0:
        uptime_str += f"{minutes} دقیقه و "
    uptime_str += f"{seconds} ثانیه"
    return uptime_str

# تابع برای پردازش پیام‌های کاربر (برای پینگ)
def handle_message(update, context):
    if 'state' in context.user_data and context.user_data['state'] == 'awaiting_ping_target':
        target = update.message.text
        context.user_data.pop('state') # پاک کردن حالت
        update.message.reply_text(f"در حال پینگ گرفتن از {target} با 5 بسته...")
        ping_result = run_ping(target)
        update.message.reply_text(ping_result, parse_mode='HTML')
    else:
        update.message.reply_text("لطفاً از دکمه‌ها برای شروع استفاده کنید یا /start را بزنید.")

# تابع برای اجرای دستور پینگ
def run_ping(target, count=5):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(count), target]
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if stderr:
            return f"خطا در اجرای پینگ: {stderr}"

        # تجزیه و تحلیل خروجی پینگ
        if "unknown host" in stdout.lower() or "could not find host" in stdout.lower():
            return "هاست یا IP آدرس وارد شده معتبر نیست."

        lines = stdout.splitlines()
        ping_output = []
        packet_stats = ""
        rtt_stats = ""

        for line in lines:
            ping_output.append(line)
            if "packets transmitted" in line.lower() or "packets sent" in line.lower():
                packet_stats = line
            if "rtt min/avg/max" in line.lower() or "minimum = " in line.lower():
                rtt_stats = line

        result_message = f"<b>نتیجه پینگ برای {target}:</b>\n"
        if packet_stats:
            result_message += f"<code>{packet_stats}</code>\n"
        if rtt_stats:
            result_message += f"<code>{rtt_stats}</code>\n"
        
        # اگر خروجی خاصی از میانگین و ... نبود، کل خروجی را نشان بده
        if not packet_stats and not rtt_stats:
            result_message += "<code>" + "\n".join(ping_output) + "</code>"
        
        return result_message

    except FileNotFoundError:
        return "دستور 'ping' در سیستم شما یافت نشد."
    except Exception as e:
        return f"خطایی رخ داد: {e}"

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    # <--- تغییر در اینجا: Filters.text به filters.TEXT و Filters.command به ~filters.COMMAND
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
