import sqlite3

from telegram import Update
import os
import re
import logging


class BotDB:
    def __init__(self):
        if not os.path.exists('db'):
            os.makedirs('db')

        self.con = sqlite3.connect('db/BotDB.db')
        self.cur = self.con.cursor()

        self.cur.execute('''CREATE TABLE IF NOT EXISTS messages (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `tg_user_id` INTEGER,
                           `first_name` VARCHAR(100),
                           `last_name` VARCHAR(100),
                           `username` VARCHAR(100),
                           `message` TEXT,
                           `date` VARCHAR(100))''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS subscribers (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `tg_user_id` INTEGER,
                           `is_subscriber` INTEGER,
                           `gpt_provider` VARCHAR(20))''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS youtubeUrls (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `url` TEXT UNIQUE,
                           `short_info` TEXT,
                           `video_info` TEXT,
                           `thumbnail` TEXT,
                           `title` TEXT)''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS vkUrls (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `url` TEXT UNIQUE,
                           `short_info` TEXT,
                           `video_info` TEXT,
                           `thumbnail` TEXT,
                           `title` TEXT)''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS vk_formats (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `fast` INTEGER,
                           `button_text` TEXT,
                           `emoji` VARCHAR(5),
                           `frame_size` VARCHAR(10),
                           `filesize` VARCHAR(10),
                           `format_code` VARCHAR(20),
                           `format_note` VARCHAR(20),
                           `ext` VARCHAR(5),
                           `tg_file_id` VARCHAR(100),
                           `url` VARCHAR(100),
                           `FK__vkUrls_id` INTEGER,
                           FOREIGN KEY (FK__vkUrls_id) REFERENCES vkUrls(id))''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS youtube_formats (
                           `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                           `fast` INTEGER,
                           `button_text` TEXT,
                           `emoji` VARCHAR(5),
                           `frame_size` VARCHAR(10),
                           `filesize` VARCHAR(10),
                           `format_code` VARCHAR(20),
                           `format_note` VARCHAR(20),
                           `ext` VARCHAR(5),
                           `tg_file_id` VARCHAR(100),
                           `url` VARCHAR(100),
                           `FK__youtubeUrls_id` INTEGER,
                           FOREIGN KEY (FK__youtubeUrls_id) REFERENCES youtubeUrls(id))''')

        self.con.commit()

    # --- USERS --- #

    def user_exist(self, tg_user_id: int) -> bool:
        self.cur.execute("SELECT COUNT(*) FROM `subscribers` WHERE `tg_user_id` = ?",
                         (tg_user_id,))

        if self.cur.fetchone()[0] > 0:
            return True
        else:
            return False

    def ADD_subscriber(self, update: Update):
        tg_user_id = update.message.from_user.id
        is_subscriber = 1

        self.cur.execute("INSERT INTO `subscribers` (tg_user_id, is_subscriber) VALUES (?, ?)",
                         (tg_user_id, is_subscriber,))
        self.con.commit()
        logging.info(f"""ADD new subscriber: `{update.message.from_user.first_name}` id: {tg_user_id} """)

    def ADD_user_message(self, update: Update):
        """ Сохранение сообщения от пользователя """

        try:
            tg_user_id = update.message.from_user.id
            first_name = update.message.from_user.first_name
            last_name = update.message.from_user.last_name
            username = update.message.from_user.username
            message = update.message.text
            date = update.message.date

            self.cur.execute("INSERT INTO `messages` (tg_user_id, first_name, last_name, username, message, date) VALUES (?, ?, ?, ?, ?, ?)",
                             (tg_user_id, first_name, last_name, username, message, date))
            self.con.commit()
            logging.info(f"""ADD new message: `{message}` FROM user: {tg_user_id} """)

        except Exception as e:
            logging.error(e)

    def GET_gpt_provider(self, update: Update):
        try:
            tg_user_id = update.message.from_user.id
        except Exception as e:
            logging.error(e)
            tg_user_id = update.callback_query.from_user.id

        self.cur.execute("SELECT IFNULL(`gpt_provider`, 'None') FROM `subscribers` WHERE `tg_user_id` = ?",
                         (tg_user_id,))

        provider = self.cur.fetchone()
        if provider is None:
            return None
        else:
            return provider[0]

    def SET_gpt_provider(self, update: Update):
        gpt_provider = re.search(pattern=r'>(.*?)$', string=update.callback_query.data).group(1)
        tg_user_id = update.callback_query.from_user.id

        self.cur.execute("UPDATE `subscribers` SET `gpt_provider` = ? WHERE `tg_user_id` = ?",
                         (gpt_provider, tg_user_id,))
        self.con.commit()

    # --- /USERS --- #

    ####################################################

    def close(self):
        self.con.close()
        logging.info(""" Соединение с БД закрыто """)
