import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import math

# تنظیمات لاگینگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توکن ربات خود را اینجا قرار دهید
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

class Calculator:
    def __init__(self):
        self.current = "0"
        self.previous = ""
        self.operator = ""
        self.reset_on_next = False
        
    def clear(self):
        self.current = "0"
        self.previous = ""
        self.operator = ""
        self.reset_on_next = False
        
    def add_digit(self, digit):
        if self.reset_on_next:
            self.current = "0"
            self.reset_on_next = False
            
        if self.current == "0" and digit != ".":
            self.current = digit
        elif digit == "." and "." not in self.current:
            self.current += digit
        elif digit != ".":
            if len(self.current) < 15:  # محدودیت طول
                self.current += digit
                
    def set_operator(self, op):
        if self.operator and not self.reset_on_next:
            self.calculate()
        self.previous = self.current
        self.operator = op
        self.reset_on_next = True
        
    def calculate(self):
        try:
            if not self.previous or not self.operator:
                return
                
            prev_num = float(self.previous)
            curr_num = float(self.current)
            
            if self.operator == "+":
                result = prev_num + curr_num
            elif self.operator == "-":
                result = prev_num - curr_num
            elif self.operator == "×":
                result = prev_num * curr_num
            elif self.operator == "÷":
                if curr_num == 0:
                    self.current = "خطا: تقسیم بر صفر"
                    self.reset_on_next = True
                    return
                result = prev_num / curr_num
            elif self.operator == "^":
                result = prev_num ** curr_num
            else:
                return
                
            # فرمت کردن نتیجه
            if result.is_integer():
                self.current = str(int(result))
            else:
                self.current = f"{result:.10f}".rstrip('0').rstrip('.')
                
            self.operator = ""
            self.previous = ""
            self.reset_on_next = True
            
        except (ValueError, OverflowError):
            self.current = "خطا"
            self.reset_on_next = True
            
    def scientific_operation(self, operation):
        try:
            num = float(self.current)
            
            if operation == "sin":
                result = math.sin(math.radians(num))
            elif operation == "cos":
                result = math.cos(math.radians(num))
            elif operation == "tan":
                result = math.tan(math.radians(num))
            elif operation == "log":
                if num <= 0:
                    self.current = "خطا: لگاریتم عدد منفی"
                    self.reset_on_next = True
                    return
                result = math.log10(num)
            elif operation == "ln":
                if num <= 0:
                    self.current = "خطا: لگاریتم عدد منفی"
                    self.reset_on_next = True
                    return
                result = math.log(num)
            elif operation == "sqrt":
                if num < 0:
                    self.current = "خطا: ریشه عدد منفی"
                    self.reset_on_next = True
                    return
                result = math.sqrt(num)
            elif operation == "x²":
                result = num ** 2
            elif operation == "x³":
                result = num ** 3
            elif operation == "1/x":
                if num == 0:
                    self.current = "خطا: تقسیم بر صفر"
                    self.reset_on_next = True
                    return
                result = 1 / num
            elif operation == "π":
                result = math.pi
            elif operation == "e":
                result = math.e
            else:
                return
                
            # فرمت کردن نتیجه
            if result.is_integer():
                self.current = str(int(result))
            else:
                self.current = f"{result:.10f}".rstrip('0').rstrip('.')
                
            self.reset_on_next = True
            
        except (ValueError, OverflowError):
            self.current = "خطا"
            self.reset_on_next = True

# ذخیره ماشین حساب برای هر کاربر
user_calculators = {}

def get_calculator_keyboard():
    """ایجاد کلیدهای ماشین حساب"""
    keyboard = [
        [
            InlineKeyboardButton("C", callback_data="clear"),
            InlineKeyboardButton("⌫", callback_data="backspace"),
            InlineKeyboardButton("^", callback_data="power"),
            InlineKeyboardButton("÷", callback_data="divide")
        ],
        [
            InlineKeyboardButton("7", callback_data="7"),
            InlineKeyboardButton("8", callback_data="8"),
            InlineKeyboardButton("9", callback_data="9"),
            InlineKeyboardButton("×", callback_data="multiply")
        ],
        [
            InlineKeyboardButton("4", callback_data="4"),
            InlineKeyboardButton("5", callback_data="5"),
            InlineKeyboardButton("6", callback_data="6"),
            InlineKeyboardButton("-", callback_data="subtract")
        ],
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
            InlineKeyboardButton("3", callback_data="3"),
            InlineKeyboardButton("+", callback_data="add")
        ],
        [
            InlineKeyboardButton("±", callback_data="sign"),
            InlineKeyboardButton("0", callback_data="0"),
            InlineKeyboardButton(".", callback_data="decimal"),
            InlineKeyboardButton("=", callback_data="equals")
        ],
        [
            InlineKeyboardButton("🔬 علمی", callback_data="scientific"),
            InlineKeyboardButton("📊 تبدیل", callback_data="convert"),
            InlineKeyboardButton("📜 تاریخچه", callback_data="history")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_scientific_keyboard():
    """ایجاد کلیدهای ماشین حساب علمی"""
    keyboard = [
        [
            InlineKeyboardButton("sin", callback_data="sin"),
            InlineKeyboardButton("cos", callback_data="cos"),
            InlineKeyboardButton("tan", callback_data="tan"),
            InlineKeyboardButton("π", callback_data="pi")
        ],
        [
            InlineKeyboardButton("log", callback_data="log"),
            InlineKeyboardButton("ln", callback_data="ln"),
            InlineKeyboardButton("√", callback_data="sqrt"),
            InlineKeyboardButton("e", callback_data="e")
        ],
        [
            InlineKeyboardButton("x²", callback_data="x2"),
            InlineKeyboardButton("x³", callback_data="x3"),
            InlineKeyboardButton("1/x", callback_data="reciprocal"),
            InlineKeyboardButton("!", callback_data="factorial")
        ],
        [
            InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_basic")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_converter_keyboard():
    """ایجاد کلیدهای تبدیل واحد"""
    keyboard = [
        [
            InlineKeyboardButton("طول", callback_data="length_convert"),
            InlineKeyboardButton("وزن", callback_data="weight_convert")
        ],
        [
            InlineKeyboardButton("دما", callback_data="temp_convert"),
            InlineKeyboardButton("ارز", callback_data="currency_convert")
        ],
        [
            InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_basic")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات"""
    user_id = update.effective_user.id
    user_calculators[user_id] = Calculator()
    
    welcome_text = """
🧮 *ماشین حساب پیشرفته* 🧮

سلام! من ماشین حساب هوشمند شما هستم.

🔹 ماشین حساب پایه
🔹 ماشین حساب علمی  
🔹 تبدیل واحدها
🔹 ذخیره تاریخچه

برای شروع، از کلیدهای زیر استفاده کنید:
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_calculator_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیدها"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # ایجاد ماشین حساب برای کاربر جدید
    if user_id not in user_calculators:
        user_calculators[user_id] = Calculator()
    
    calc = user_calculators[user_id]
    data = query.data
    
    await query.answer()
    
    # مدیریت اعداد
    if data.isdigit():
        calc.add_digit(data)
    
    # مدیریت اعمال ریاضی
    elif data == "add":
        calc.set_operator("+")
    elif data == "subtract":
        calc.set_operator("-")
    elif data == "multiply":
        calc.set_operator("×")
    elif data == "divide":
        calc.set_operator("÷")
    elif data == "power":
        calc.set_operator("^")
    
    # مدیریت عملیات خاص
    elif data == "equals":
        calc.calculate()
    elif data == "clear":
        calc.clear()
    elif data == "decimal":
        calc.add_digit(".")
    elif data == "backspace":
        if len(calc.current) > 1:
            calc.current = calc.current[:-1]
        else:
            calc.current = "0"
    elif data == "sign":
        if calc.current != "0":
            if calc.current.startswith("-"):
                calc.current = calc.current[1:]
            else:
                calc.current = "-" + calc.current
    
    # عملیات علمی
    elif data in ["sin", "cos", "tan", "log", "ln", "sqrt", "x2", "x3", "reciprocal"]:
        operation_map = {
            "x2": "x²",
            "x3": "x³",
            "reciprocal": "1/x"
        }
        op = operation_map.get(data, data)
        calc.scientific_operation(op)
    elif data == "pi":
        calc.scientific_operation("π")
    elif data == "e":
        calc.scientific_operation("e")
    
    # تغییر حالت کلیدها
    elif data == "scientific":
        await query.edit_message_text(
            f"🔬 *ماشین حساب علمی*\n\n`{calc.current}`",
            parse_mode='Markdown',
            reply_markup=get_scientific_keyboard()
        )
        return
    elif data == "convert":
        await query.edit_message_text(
            "🔄 *تبدیل واحدها*\n\nنوع تبدیل مورد نظر را انتخاب کنید:",
            parse_mode='Markdown',
            reply_markup=get_converter_keyboard()
        )
        return
    elif data == "back_to_basic":
        await query.edit_message_text(
            f"🧮 *ماشین حساب*\n\n`{calc.current}`",
            parse_mode='Markdown',
            reply_markup=get_calculator_keyboard()
        )
        return
    elif data == "history":
        await query.edit_message_text(
            "📜 *تاریخچه محاسبات*\n\n(قابلیت تاریخچه در نسخه آینده اضافه خواهد شد)",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_basic")]])
        )
        return
    
    # بروزرسانی صفحه نمایش
    display_text = f"🧮 *ماشین حساب*\n\n`{calc.current}`"
    if calc.operator and calc.previous:
        display_text = f"🧮 *ماشین حساب*\n\n`{calc.previous} {calc.operator} {calc.current}`"
    
    await query.edit_message_text(
        display_text,
        parse_mode='Markdown',
        reply_markup=get_calculator_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش راهنما"""
    help_text = """
📚 *راهنمای استفاده*

🔸 *ماشین حساب پایه:*
• اعداد، اعمال چهارگانه
• توان، ریشه، درصد

🔸 *ماشین حساب علمی:*  
• توابع مثلثاتی (sin, cos, tan)
• لگاریتم (log, ln)
• ثوابت ریاضی (π, e)

🔸 *کلیدهای ویژه:*
• C: پاک کردن کامل
• ⌫: پاک کردن آخرین رقم  
• ±: تغییر علامت

💡 *نکات:*
• از `/start` برای شروع مجدد استفاده کنید
• از `/calc` برای باز کردن ماشین حساب استفاده کنید
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """باز کردن ماشین حساب"""
    user_id = update.effective_user.id
    if user_id not in user_calculators:
        user_calculators[user_id] = Calculator()
    
    calc = user_calculators[user_id]
    
    await update.message.reply_text(
        f"🧮 *ماشین حساب*\n\n`{calc.current}`",
        parse_mode='Markdown',
        reply_markup=get_calculator_keyboard()
    )

def main():
    """اجرای اصلی ربات"""
    # توکن ربات را اینجا وارد کنید
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً توکن ربات خود را در متغیر BOT_TOKEN وارد کنید")
        print("💡 توکن را از @BotFather در تلگرام دریافت کنید")
        return
    
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("calc", calc_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # شروع ربات
    print("🚀 ربات ماشین حساب شروع شد...")
    print("📱 برای توقف ربات از Ctrl+C استفاده کنید")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
