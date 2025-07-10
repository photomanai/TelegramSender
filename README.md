# Telegram Invite App

This project is an application that interacts with users via the Telegram bot and sends invitation messages to specific users based on username matches. It operates through the Telegram API.

## Getting Started

Before running the project, follow the setup instructions below.

### Requirements

- Python 3.7+
- `telethon` library
- `python-dotenv` library

### Installation

1. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/photomanai/TelegramSender.git
   ```

2. Navigate to the project directory:
   ```bash
   cd TelegramSender
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add your `API_ID` and `API_HASH` values obtained from Telegram API:
   ```text
   API_ID=your_api_id
   API_HASH=your_api_hash
   ```

### Usage

1. Run the Python script to start the bot:
   ```bash
   python appServer.py
   ```

2. Once the bot starts, it will send messages to users whose names match the ones in the `selected_names` list.

### Features

- Lists all dialogs using the Telegram API.
- Sends messages to users whose names match the ones in `selected_names`.
- Asynchronous processing for faster performance.

## Contributing

If you want to contribute to this project, feel free to send a pull request. If you have any questions or need help, don't hesitate to contact us.

## License

This project is licensed under the MIT License.
