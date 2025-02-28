import os
import logging
import re
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Expense Tracker')
DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')
ALLOWED_USER_IDS = [int(id) for id in os.getenv('ALLOWED_USER_IDS').split(',')]
PHOTO_TTL = 300  # 5 minutes in seconds

# Google Services Setup
credentials_json = os.getenv('GOOGLE_CREDS')

# Parse the JSON string
if credentials_json:
    credentials_dict = json.loads(credentials_json)
else:
    # Handle the case when credentials_json is None
    print("Error: Google credentials not found in environment variables.")
    exit(1)

# Define the scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Create credentials object from the parsed JSON
CREDS = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)

# Authorize the client
client = gspread.authorize(CREDS)

spreadsheet = client.open(GOOGLE_SHEET_NAME)
log_sheet = spreadsheet.worksheet('Transactions')  # Rename your data sheet
dashboard_sheet = spreadsheet.worksheet('Dashboard')

drive_service = build('drive', 'v3', credentials=CREDS)

# Session storage
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USER_IDS:
        return
    await update.message.reply_text(
        "💰 Expense Tracker Bot\n\n"
        "Send receipt photo first, then expense in format:\n"
        "<category> <amount> [remarks]\n"
        "Example: Food 500 Dinner with friends")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            return

        photo_file = await update.message.photo[-1].get_file()
        file_name = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        await photo_file.download_to_drive(file_name)

        file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(file_name, mimetype='image/jpeg')
        drive_file = drive_service.files().create(
            body=file_metadata, media_body=media,
            fields='id, webViewLink').execute()

        user_sessions[user_id] = {
            'receipt_url': drive_file['webViewLink'],
            'timestamp': datetime.now()
        }

        os.remove(file_name)
        await update.message.reply_text(
            "📷 Receipt saved! Now send expense details")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USER_IDS:
        return

    text = update.message.text
    try:
        # Check for expired receipts
        if user_id in user_sessions:
            time_diff = (datetime.now() -
                         user_sessions[user_id]['timestamp']).total_seconds()
            if time_diff > PHOTO_TTL:
                del user_sessions[user_id]
                await update.message.reply_text(
                    "⌛ Receipt expired. Please resend photo first.")
                return

        match = re.match(r'(\w+)\s+(\d+)(?:\s+(.*))?', text)
        if not match:
            raise ValueError("Invalid format")

        category, amount, remarks = match.groups()
        receipt_url = user_sessions.get(user_id, {}).get('receipt_url', '')

        if user_id in user_sessions:
            del user_sessions[user_id]
        current_date_time = datetime.now().isoformat()
        row = [
            category.capitalize(),
            float(amount), remarks or '', current_date_time, receipt_url
        ]

        log_sheet.append_row(row)
        response = f"✅ Added: {category} ₹{amount}"
        if receipt_url:
            response += f"\n📎 Receipt: {receipt_url}"

        await update.message.reply_text(response)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\nUse format: Category Amount [Remarks]")


async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USER_IDS:
        return

    try:
        monthly_total = dashboard_sheet.acell('A2').value

        # Get category names and totals
        category_names = dashboard_sheet.col_values(2)[
            3:]  # Get data from "C" Col excluding headers and total
        category_totals = dashboard_sheet.col_values(3)[
            3:]  # Get Data from "D" col excluding headers and total.

        # Build the category breakdown string
        breakdown_text = ""
        for name, total in zip(category_names, category_totals):
            breakdown_text += f"{name}: ₹{total}\n"

        await update.message.reply_text(
            f"📊 Monthly Report\nTotal: ₹{monthly_total}\nBreakdown:\n{breakdown_text}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Report error: {str(e)}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", monthly_report))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense))

    application.run_polling()
