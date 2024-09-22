import os
import json
import base64
import imaplib
import email
from google.oauth2 import service_account
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ngeload service account credentials 
SERVICE_ACCOUNT_FILE = 'path_to_your_service_account.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# ngebuat service account credentials objek
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

# ngehandle email user biar bisa diakses tanpa pw
DELEGATED_EMAIL = 'user_email_to_access@gmail.com'

# nganuin Gmail API client
credentials = credentials.with_subject(DELEGATED_EMAIL)
service = build('gmail', 'v1', credentials=credentials)

async def get_otp_from_email():
    # memakai Gmail API untuk mengakses user inbox
    result = service.users().messages().list(userId='me', q='Your OTP is').execute()
    messages = result.get('messages', [])

    for message in messages[::-1]:  # ngecek email terbaru
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        payload = msg['payload']
        parts = payload.get('parts', [])

        for part in parts:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                if 'Your OTP is' in body:
                    otp = body.split('Your OTP is ')[1].strip()
                    return otp

    return None

user_email_mapping = {}  # menyimpan user email addresses

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome! Please send your email address to use the bot.')

async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_email_mapping[user_id] = update.message.text  # nyambung ke user_email_mapping
    await update.message.reply_text(f'Email address {update.message.text} saved!')

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    email_address = user_email_mapping.get(user_id)

    if not email_address:
        await update.message.reply_text('Please set your email address first using /start.')
        return

    otp = await get_otp_from_email(email_address)  # otak atik nih fungsi buat nerima email
    if otp:
        await update.message.reply_text(f'Your OTP is: {otp}')
    else:
        await update.message.reply_text('Could not retrieve OTP. Please try again.')

#fungsi main buat manggil command bot
def main():
    application = ApplicationBuilder().token('YOUR_TELEGRAM_BOT_TOKEN').build() 
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setemail", set_email)) 
    application.add_handler(CommandHandler("getotp", get_otp))
    application.run_polling()

if __name__ == '__main__':
    main()
