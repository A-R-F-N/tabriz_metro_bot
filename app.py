import pandas as pd
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import asyncio

# توکن ربات
TOKEN = '7600866536:AAErQiOFJJYDNE5_ZUaynC7hZl7a4h0UdnM'

# لینک‌های CSV از گوگل شیت
GOING_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ZaM_EHDbNMMjS3wPcgkjuXdiHqAmdsZrsDc-Vgnua9w/pub?output=csv'
RETURN_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1hM_tNVCgDfWfUmLUAy5B9CPanyltH10VvWeDc_IvftI/pub?output=csv'

# خوندن زمان‌بندی‌ها
going_schedule = pd.read_csv(GOING_SHEET_URL)
return_schedule = pd.read_csv(RETURN_SHEET_URL)

# لیست ایستگاه‌ها
stations = [str(i) for i in range(1, 19)]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[station] for station in stations]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text('ایستگاه مبدا رو انتخاب کن:', reply_markup=reply_markup)
    return 'SELECT_FROM'

async def select_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['from_station'] = update.message.text
    keyboard = [[station] for station in stations]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text('حالا ایستگاه مقصد رو انتخاب کن:', reply_markup=reply_markup)
    return 'SELECT_TO'

async def select_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_station = int(context.user_data['from_station'])
    to_station = int(update.message.text)
    
    if from_station >= 15 or to_station >= 15:
        await update.message.reply_text('ایستگاه‌های 15 تا 18 فعلاً غیرفعال هستن!')
        return await start(update, context)

    if from_station < to_station:
        schedule = going_schedule
        direction = "رفت"
        from_col = f'Station_{from_station}'
        to_col = f'Station_{to_station}'
    elif from_station > to_station:
        schedule = return_schedule
        direction = "برگشت"
        from_col = f'Station_{from_station}'
        to_col = f'Station_{to_station}'
    else:
        await update.message.reply_text('مبدا و مقصد نمی‌تونن یکی باشن!')
        return await start(update, context)

    now = datetime.now().strftime('%H:%M')
    now_time = datetime.strptime(now, '%H:%M')

    upcoming_trips = []
    for index, row in schedule.iterrows():
        dep_time_str = row[from_col]
        arr_time_str = row[to_col]
        
        if dep_time_str == '*' or arr_time_str == '*':
            continue
        
        dep_time = datetime.strptime(dep_time_str, '%H:%M')
        arr_time = datetime.strptime(arr_time_str, '%H:%M')
        if dep_time > now_time:
            time_diff = (dep_time - now_time).total_seconds() / 60
            travel_duration = (arr_time - dep_time).total_seconds() / 60
            upcoming_trips.append((dep_time_str, arr_time_str, time_diff, travel_duration))

    if not upcoming_trips:
        await update.message.reply_text(f'امروز دیگه مترویی برای مسیر {direction} نیست!')
    else:
        upcoming_trips.sort(key=lambda x: x[2])
        response = f'نزدیک‌ترین زمان‌ها برای مسیر {direction} (از ایستگاه {from_station} به {to_station}):\n\n'
        for i, (dep, arr, diff, duration) in enumerate(upcoming_trips[:max(3, len(upcoming_trips))], 1):
            response += (f"{i}. حرکت: {dep} (در {int(diff)} دقیقه)\n"
                        f"   مدت سفر: {int(duration)} دقیقه\n"
                        f"   رسیدن: {arr}\n\n")
        await update.message.reply_text(response)
    
    return await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    from telegram.ext import ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'SELECT_FROM': [MessageHandler(filters.TEXT & ~filters.COMMAND, select_from)],
            'SELECT_TO': [MessageHandler(filters.TEXT & ~filters.COMMAND, select_to)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
