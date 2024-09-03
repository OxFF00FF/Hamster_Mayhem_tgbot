# import platform
import logging
import os
from dotenv import load_dotenv

from colors import *
from telegram_bot import HamsterPromocodeGeneratorTelegramBot


def main():
    # Read .env file
    load_dotenv()

    # Setup logging
    logging.basicConfig(format=f'{WHITE}%(asctime)s - %(name)s - %(levelname)s |  %(message)s  |  %(filename)s - def: %(funcName)s - line: %(lineno)d{RESET}', level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Check if the required environment variables are set
    required_values = ['TELEGRAM_BOT_TOKEN']
    missing_values = [value for value in required_values if os.environ.get(value) is None]
    if len(missing_values) > 0:
        logging.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)

    telegram_config = {
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
        'bot_username': os.environ.get('TELEGRAM_BOT_USERNAME', 'n/a'),
        'bot_language': os.environ.get('BOT_LANGUAGE', 'ru'),
        'chat_id': int(os.environ.get('CHAT_ID')),
    }

    telegram_bot = HamsterPromocodeGeneratorTelegramBot(config=telegram_config)

    # (python {platform.python_version()})
    # tg://resolve?domain=aesthatics_nickname_bot
    # t.me/examplebot?startgroup=true
    # t.me/examplebot?start=<ваш текст>
    logging.info(f"Bot started As `{telegram_config['bot_username'].capitalize()}` · https://t.me/{telegram_config['bot_username'].capitalize()}")

    telegram_bot.run()


if __name__ == '__main__':
    main()
