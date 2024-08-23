from __future__ import annotations

import asyncio
import datetime
import logging
import os
import random
import re
import subprocess
import sys
import time
import uuid
from typing import Any

import aiohttp
import requests
from telegram import BotCommand, BotCommandScopeAllGroupChats, Update, constants, InputMediaAnimation, InputMediaPhoto
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, Application

import Keyboards as kb
from utils import _error_gif, _hamster_key, _game_image, _loading_gif, _combo_image, remain_time, text_to_morse
from utils import get_thread_id, error_handler, get_games_data
from Hamster import HamsterKombatClicker
from db_SQlite import BotDB

db = BotDB()


# --------------------------------------------------- #
#  Перезагрузка бота
async def restart(__, _):
    logging.info('Restarting bot...')
    subprocess.Popen([sys.executable, sys.argv[0]])
    os.kill(os.getpid(), 9)


# --------------------------------------------------- #

HAMSTER_TOKEN = os.getenv('HAMSTER_TOKEN_1')
hamster_client = HamsterKombatClicker(HAMSTER_TOKEN)


class HamsterPromocodeGeneratorTelegramBot:
    def __init__(self, config: dict):
        self.config = config
        self.commands = [
            BotCommand(command='promocodes', description="Получить промокоды"),
            BotCommand(command='daily_info', description="Информация о комбо и шифре сегодня"),
            BotCommand(command='help', description="Показать справочное сообщение"),
            BotCommand(command='info', description="Информация о проекте"),
        ]
        self.group_commands = [BotCommand(command='chat', description="chat_description")] + self.commands

        self.games_data = get_games_data()['apps']

    async def get_promocodes(self, update, context):
        user_id = update.callback_query.from_user.id
        prefix = context.user_data['prefix']
        count = context.user_data['keys_count']

        progress_lock = asyncio.Lock()
        total_progress = 0

        loading_message = await context.bot.send_message(chat_id=user_id, text=f"⏳")

        for promo in self.games_data:
            if promo['prefix'] == prefix:
                APP_TOKEN = promo['appToken']
                PROMO_ID = promo['promoId']
                EVENTS_DELAY = promo['registerEventTimeout']
                EVENTS_COUNT = promo['eventsCount']

        async def _delay_random():
            return random.random() / 3 + 1

        async def _generate_client_id() -> str:
            timestamp = int(time.time() * 1000)
            random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(19)])
            return f"{timestamp}-{random_numbers}"

        async def _get_client_token(session, client_id) -> Any | None:
            url = 'https://api.gamepromo.io/promo/login-client'
            headers = {'Content-Type': 'application/json'}
            payload = {'appToken': APP_TOKEN, 'clientId': client_id, 'clientOrigin': 'deviceid'}

            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    response.raise_for_status()
                    return data['clientToken']

            except requests.exceptions.HTTPError as http_error:
                if response.status_code == 429:
                    logging.error(f"🚫  Не удалось начать генерацию. Превышено количетсво запросов")
                    return None
                else:
                    logging.error(http_error)

        async def _emulate_progress(session, client_token) -> Any | None:
            url = 'https://api.gamepromo.io/promo/register-event'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {client_token}'}
            payload = {'promoId': PROMO_ID, 'eventId': str(uuid.uuid4()), 'eventOrigin': 'undefined'}

            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    response.raise_for_status()
                    return data['hasCode']

            except requests.exceptions.HTTPError as http_error:
                if response.status_code == 429:
                    logging.error(f"🚫  Не удалось начать генерацию. Превышено количетсво запросов")
                    return None
                else:
                    logging.error(http_error)

        async def _get_promocode(session, client_token) -> Any | None:
            url = 'https://api.gamepromo.io/promo/create-code'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {client_token}'}
            payload = {'promoId': PROMO_ID}

            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    response.raise_for_status()
                    return data['promoCode']

            except requests.exceptions.HTTPError as http_error:
                if response.status_code == 429:
                    logging.error(f"🚫  Не удалось начать генерацию. Превышено количетсво запросов")
                    return None
                else:
                    logging.error(http_error)

        async def _key_generation(session, keys_count, progress_increment) -> str | None:
            global total_progress
            client_id = await _generate_client_id()
            client_token = await _get_client_token(session, client_id)

            for _ in range(EVENTS_COUNT):
                await asyncio.sleep(EVENTS_DELAY * await _delay_random() / 1000)
                has_code = await _emulate_progress(session, client_token)

                async with progress_lock:
                    total_progress += progress_increment
                    overall_progress = (total_progress / (keys_count * EVENTS_COUNT)) * 100
                    text = f"💠  Прогресс: {overall_progress:.0f}%"

                    await context.bot.edit_message_text(chat_id=user_id, message_id=loading_message.message_id, text=text)
                    logging.info(f"{prefix} · {overall_progress:.0f}% · User: {user_id}")

                if has_code:
                    break

            return await _get_promocode(session, client_token)

        async def generate(keys_count):
            global total_progress
            total_progress = 0
            progress_increment = 1

            async with aiohttp.ClientSession() as session:
                tasks = [_key_generation(session, keys_count, progress_increment) for _ in range(keys_count)]
                keys = await asyncio.gather(*tasks)
            return [key for key in keys if key]

        try:
            return await generate(count)
        except Exception as e:
            logging.error(e)
        finally:
            await context.bot.delete_message(chat_id=user_id, message_id=loading_message.message_id)

    async def save_message(self, update, context):
        db.ADD_user_message(update)
        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  New message: `{update.message.text}`\n🙍‍♂️  From user: {update.message.from_user.name}")

    async def start_generate(self, update, context):
        bot_message = update.callback_query.message.message_id
        user_id = update.callback_query.from_user.id
        prefix = context.user_data['prefix']
        keys_count = context.user_data['keys_count']
        keyboard = kb.close_InlineKeyboard

        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  Generate: `{prefix} · {keys_count}`\n🙍‍♂️  For user: {user_id}")

        try:
            for promo in self.games_data:
                if promo['prefix'] == prefix:
                    EVENTS_DELAY = promo['registerEventTimeout']
                    EVENTS_COUNT = promo['eventsCount']
                    TITLE = promo['title']
                    TEXT = promo['text']
                    EMOJI = promo['emoji']
            remain = remain_time((EVENTS_COUNT * EVENTS_DELAY) / 1000)
            text = f"<b>{TEXT}\n\n🎁  Генерируется промокодов: {keys_count}\n⏳  ~ {remain}</b>"
            loading = InputMediaAnimation(media=_loading_gif(), caption=text, parse_mode=constants.ParseMode.HTML)
            await context.bot.edit_message_media(chat_id=user_id, media=loading, message_id=bot_message)

            promocodes = await self.get_promocodes(update, context)
            result = f"<b>{EMOJI} {TITLE}\n\nПромокоды: </b>\n"
            for promocode in promocodes:
                result += f"·  <code>{promocode}</code>\n"

            image = InputMediaPhoto(media=_game_image(prefix), caption=result, parse_mode=constants.ParseMode.HTML)
            await context.bot.edit_message_media(chat_id=user_id, reply_markup=keyboard, media=image, message_id=bot_message)

        except Exception as e:
            logging.error(e)
            error = InputMediaAnimation(media=_error_gif(), caption=f'🙁  Во время генерации произошла ошибка')
            await update.callback_query.edit_message_media(media=error, reply_markup=keyboard)

    # ########################################################################################## #
    # -------------------------------- COMMANDS ------------------------------------------------ #

    async def start(self, update: Update, context):
        """
        Shows the start menu.
        """
        db.ADD_user_message(update)
        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  New message: <b>`{update.message.text}`</b>\n\n🙍‍♂️  From user: <b>`{update.message.from_user.name}`</b>", parse_mode=constants.ParseMode.HTML)

        user_name = update.message.from_user.first_name
        welcome_message = f"🤝  Добро пожаловать <b>{user_name}</b>\n"
        hello_message = f"✋  Привет <b>{user_name}</b>\n"
        keyboard = kb.close_InlineKeyboard
        if not db.user_exist(update.effective_message.from_user.id):
            db.ADD_subscriber(update)
            await context.bot.send_message(chat_id=self.config['chat_id'], text=f"🌟  New Subscriber: <b>`{user_name}`</b>\n🆔  ID: {update.message.from_user.id}", parse_mode=constants.ParseMode.HTML)
            await update.message.reply_text(welcome_message, reply_markup=keyboard, parse_mode=constants.ParseMode.HTML)
        else:
            await update.message.reply_text(text=hello_message, reply_markup=keyboard, parse_mode=constants.ParseMode.HTML)

    async def help(self, update: Update, context) -> None:
        db.ADD_user_message(update)
        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  New message: `{update.message.text}`\n🙍‍♂️  From user: {update.message.from_user.name}")

        help_text = f"help text"
        await update.message.reply_text(help_text, disable_web_page_preview=True, parse_mode=constants.ParseMode.MARKDOWN)

    async def info(self, update: Update, context) -> None:
        db.ADD_user_message(update)
        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  New message: `{update.message.text}`\n\n🙍‍♂️  From user: {update.message.from_user.name}")

        info_text = f"info text"
        await update.message.reply_text(info_text, disable_web_page_preview=True, parse_mode=constants.ParseMode.MARKDOWN)

    async def daily_info(self, update:Update, context):
        db.ADD_user_message(update)
        await context.bot.send_message(chat_id=self.config['chat_id'], text=f"📩  New message: `{update.message.text}`\n\n🙍‍♂️  From user: {update.message.from_user.name}")

        user_id = update.message.from_user.id
        loading_message = await context.bot.send_message(chat_id=user_id, text=f"⏳")
        try:
            cipher = hamster_client._get_daily_cipher()
            combo = hamster_client._get_daily_combo()
            morse = text_to_morse(cipher)
            today = datetime.datetime.today().date()
            total_price, total_profit, cards, cards_info = 0, 0, [], ''
            upgradesForBuy = hamster_client.upgrades_for_buy()

            info = f"📆  {today} (текущая дата)\n📆  {combo['date']} (дата комбо) \n\n"
            combo_summary = f"🏆  Комбо: \n"
            for upgradeId in combo['combo']:
                for upgrade in upgradesForBuy:
                    if upgradeId == upgrade['id']:
                        if upgrade['isAvailable'] and not upgrade['isExpired']:
                            total_price += upgrade['price']
                            total_profit += upgrade['profitPerHourDelta']
                            combo_summary += f"🏷  <b>{upgrade['name']} · {upgrade['section']}</b> \n"
            info += f"{combo_summary} \n"
            info += f"🔎  Шифр:\n<b>{cipher}\n{morse}</b>"

            keyboard = kb.close_InlineKeyboard
            await update.message.reply_photo(photo=_combo_image(), caption=info, reply_markup=keyboard, parse_mode=constants.ParseMode.HTML)

        except Exception as e:
            logging.error(e)

        finally:
            await context.bot.delete_message(chat_id=user_id, message_id=loading_message.message_id)

    async def promocodes(self, update: Update, _):
        db.ADD_user_message(update)

        keyboard = kb.promocodes_InlineKeyboard()
        text = '<b>Для какой игры хотите получить промокоды?</b>'
        await update.message.reply_photo(photo=_hamster_key(), caption=text, reply_markup=keyboard, message_thread_id=get_thread_id(update), parse_mode=constants.ParseMode.HTML)

    # -------------------------------- /COMMANDS ----------------------------------------------- #
    # ########################################################################################## #

    # ########################################################################################### #
    # ------------------------ CallBack handlers ------------------------------------------------ #

    async def callback_close(self, update: Update, context):
        user_id = update.callback_query.from_user.id
        bot_message_id = update.callback_query.message.message_id

        callback_data = update.callback_query.data
        logging.info(f"Callbackdata: `{callback_data}` FROM user: {user_id}")

        if callback_data.startswith('close'):
            await context.bot.delete_message(chat_id=user_id, message_id=bot_message_id)

    async def callback_choose_promo(self, update: Update, context):
        bot_message = update.callback_query.message.message_id
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data
        logging.info(f"Callbackdata: `{callback_data}` FROM user: {user_id}")

        match = re.search(pattern=r'>(.*?)$', string=callback_data)
        if match:
            prefix = match.group(1)
            context.user_data['prefix'] = prefix

        for promo in self.games_data:
            if promo['prefix'] == prefix:
                text = f"<b>Сколько промокодов хотите получить?</b>"

        keyboard = kb.promocodes_count_InlineKeyboard()
        image = InputMediaPhoto(media=_game_image(prefix), caption=text, parse_mode=constants.ParseMode.HTML)
        await context.bot.edit_message_media(chat_id=user_id, media=image, reply_markup=keyboard, message_id=bot_message)

    async def callback_choose_count(self, update: Update, context):
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data
        logging.info(f"Callbackdata: `{callback_data}` FROM user: {user_id}")

        match = re.search(pattern=r'>(.*?)$', string=callback_data)
        if match:
            context.user_data['keys_count'] = int(match.group(1))
        await self.start_generate(update, context)

    # ------------------------- /CallBack handlers ---------------------------------------------- #
    # ########################################################################################### #

    async def post_init(self, application: Application) -> None:
        """
        Post initialization hook for the bot.
        """
        await application.bot.set_my_commands(self.group_commands, scope=BotCommandScopeAllGroupChats())
        await application.bot.set_my_commands(self.commands)

    def run(self):
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """
        application = ApplicationBuilder() \
            .token(self.config['token']) \
            .post_init(self.post_init) \
            .concurrent_updates(True) \
            .connect_timeout(30) \
            .read_timeout(30) \
            .build()

        # command handlers
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CommandHandler('help', self.help))
        application.add_handler(CommandHandler('info', self.info))
        application.add_handler(CommandHandler('restart', restart))

        application.add_handler(CommandHandler('daily_info', self.daily_info))
        application.add_handler(CommandHandler('promocodes', self.promocodes))

        # message handlers
        application.add_handler(MessageHandler(filters.TEXT, self.save_message))

        # callback handlers
        application.add_handler(CallbackQueryHandler(self.callback_close, pattern=r'^close'))
        application.add_handler(CallbackQueryHandler(self.callback_choose_promo, pattern=r'^promo>'))
        application.add_handler(CallbackQueryHandler(self.callback_choose_count, pattern=r'^generate_count>'))

        # error handlers
        application.add_error_handler(error_handler)

        application.run_polling(drop_pending_updates=True)
