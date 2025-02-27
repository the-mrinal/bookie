# Expense Tracker Bot

## Overview
The Expense Tracker Bot is a Telegram bot that allows users to track their expenses by sending receipt photos and expense details. The bot saves the receipt images to Google Drive and logs the expense details in a Google Sheet.

## Features
- Upload receipt photos to Google Drive.
- Log expenses with categories, amounts, and optional remarks.
- Generate monthly expense reports with category breakdowns.

## Prerequisites
- Python 3.7+
- A Google Cloud project with Google Drive and Google Sheets APIs enabled.
- A Telegram bot token.
- `credentials.json` file for Google API authentication.
- `.env` file with necessary environment variables.

## Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd expense_tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file in the root directory and add the following variables:
   ```
   TELEGRAM_TOKEN=your-telegram-token
   GOOGLE_SHEET_NAME=Expense Tracker
   DRIVE_FOLDER_ID=your-drive-folder-id
   ALLOWED_USER_IDS=comma-separated-user-ids
   ```

4. **Google API Credentials**
   - Place your `credentials.json` file in the root directory.
   - Ensure it has access to the Google Drive and Sheets APIs.

## Running the Bot
Run the bot using the following command:
```bash
python bot.py
```

## Usage
- **Start the Bot**: Send `/start` to the bot to receive instructions.
- **Upload Receipt**: Send a photo of the receipt.
- **Log Expense**: Send a message in the format `<category> <amount> [remarks]`.
- **Monthly Report**: Send `/report` to get a summary of expenses.

## Debugging
- Use VS Code or Cursor to set breakpoints and debug the bot.
- Ensure all environment variables and credentials are correctly set.

## License
This project is licensed under the MIT License.

## Contributing
Feel free to submit issues or pull requests for improvements or bug fixes. 