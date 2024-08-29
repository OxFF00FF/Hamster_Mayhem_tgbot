from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_games_data

# кнопка закрыть
close_button = InlineKeyboardButton("❌  Закрыть", callback_data='close')
close_InlineKeyboard = InlineKeyboardMarkup([[close_button]])

# кнопка назад к играм
back_button = InlineKeyboardButton("↩️  Назад", callback_data=f'back_to_games')


def fold_button(url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton("🔼  Свернуть", callback_data=f'fold>{url}')


def close_fold_InlineKeyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[fold_button(url), close_button]])


def unfold_InlineKeyboard(url: str) -> InlineKeyboardMarkup:
    unfold_button = InlineKeyboardButton("🔽  Развернуть", callback_data=f'unfold>{url}')
    return InlineKeyboardMarkup([[unfold_button]])


def hamster_InlineKeyboard() -> InlineKeyboardMarkup:
    cooldowns = {}

    if cooldowns['taps']:
        complete_taps_button = InlineKeyboardButton(f"👆  Клики  ℹ️", callback_data=f'complete_taps')
    else:
        complete_taps_button = InlineKeyboardButton(f"👆  Клики  (🚫  {cooldowns['taps_remain']} минут)", callback_data=f'complete_taps')

    if cooldowns['cipher']:
        complete_chipher_button = InlineKeyboardButton("🗃 Шифр  ✅", callback_data=f'complete_cipher')
    else:
        complete_chipher_button = InlineKeyboardButton("🗃 Шифр  ℹ️", callback_data=f'complete_cipher')

    if cooldowns['key']:
        complete_keys_chipher_button = InlineKeyboardButton("🔑  Миниигра  ✅", callback_data=f'complete_keys_chipher')
    else:
        complete_keys_chipher_button = InlineKeyboardButton("🔑  Миниигра  ℹ️", callback_data=f'complete_keys_chipher')

    if cooldowns['tasks']:
        complete_tasks_button = InlineKeyboardButton("📑  Задания  ✅", callback_data=f'complete_tasks')
    else:
        complete_tasks_button = InlineKeyboardButton("📑  Задания  ℹ️", callback_data=f'complete_tasks')

    if cooldowns['combo']:
        complete_combo_button = InlineKeyboardButton("💰  Комбо  ✅", callback_data=f'complete_combo')
    else:
        complete_combo_button = InlineKeyboardButton("💰  Комбо  ℹ️", callback_data=f'complete_combo')

    promocode_button = InlineKeyboardButton("🎉  Получить промокод", callback_data=f'complete_promocode')

    return InlineKeyboardMarkup(
        [
            [complete_taps_button],
            [complete_tasks_button, complete_chipher_button, complete_combo_button],
            [complete_keys_chipher_button, promocode_button],
            [close_button]
        ]
    )


def not_all_available_InlineKeyboard() -> InlineKeyboardMarkup:
    yes_button = InlineKeyboardButton("✅  Да", callback_data=f'buy_combo')
    return InlineKeyboardMarkup([[yes_button, close_button]])


def apply_promocode_InlineKeyboard() -> InlineKeyboardMarkup:
    apply_button = InlineKeyboardButton("⚠️  Применить промокод?", callback_data=f'complete_apply_promocode')
    return InlineKeyboardMarkup([[apply_button, close_button]])


def promocodes_InlineKeyboard() -> InlineKeyboardMarkup:
    keyboard = []
    games_data = get_games_data()['apps']

    row = []
    for i, promo in enumerate(games_data):
        button_text = f"{promo['emoji']}  {promo['title']}"
        row.append(InlineKeyboardButton(text=button_text, callback_data=f"promo>{promo['prefix']}"))

        if len(row) == 2 or i == len(games_data) - 1:
            keyboard.append(row)
            row = []

    keyboard.append([close_button])
    return InlineKeyboardMarkup(keyboard)


def promocodes_count_InlineKeyboard() -> InlineKeyboardMarkup:
    one_button = InlineKeyboardButton("1️⃣", callback_data=f'generate_count>1')
    two_button = InlineKeyboardButton("2️⃣", callback_data=f'generate_count>2')
    three_button = InlineKeyboardButton("3️⃣", callback_data=f'generate_count>3')
    four_button = InlineKeyboardButton("4️⃣", callback_data=f'generate_count>4')

    return InlineKeyboardMarkup([[one_button, two_button, three_button, four_button],
                                 [back_button, close_button]])


def promocodes_result_InlineKeyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[back_button, close_button]])
