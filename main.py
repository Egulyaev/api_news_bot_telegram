import json
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'http://127.0.0.1:8000/api/v1/posts/'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)


def send_post(update, context):
    chat = update.effective_chat
    post_id = int(context.args[0])
    posts = get_posts()
    keyboard = [
        [InlineKeyboardButton(
            "Посмотреть комментарии",
            callback_data=f'post_comments:{post_id}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=chat.id,
        text=parse_post(posts[post_id]),
        reply_markup=reply_markup
    )


def send_post_list(update, context):
    chat = update.effective_chat
    posts = get_posts()
    for post in posts:
        keyboard = [
            [InlineKeyboardButton(
                "Посмотреть комментарии",
                callback_data=f"post_comments:{post['id']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=chat.id,
            text=f"{post['text']}",
            reply_markup=reply_markup
        )


def post_list_handler(update, context):
    pass


def main_handler(update, context):
    chat = update.effective_chat
    query = update.callback_query
    handler_name, *args = query.data.split(':')
    query.answer()
    if handler_name == 'comments':
        post_id = int(args[0])
        comments = get_comments(post_id)
        current_comments = int(args[1])
        end_comment = len(comments)
        if current_comments == 0:
            keyboard = [
                [
                    InlineKeyboardButton
                    ("Следующий",
                     callback_data=f'comments:'
                                   f'{post_id}:{current_comments + 1}'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text=parse_comment(comments[current_comments]),
                reply_markup=reply_markup
            )
        elif current_comments == (end_comment - 1):
            keyboard = [
                [InlineKeyboardButton(
                    "Предыдущий",
                    callback_data=f'comments:'
                                  f'{post_id}:{current_comments - 1}'
                )],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text=parse_comment(comments[current_comments]),
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton(
                    "Предыдущий",
                    callback_data=f'comments:'
                                  f'{post_id}:{current_comments - 1}'
                ),
                    InlineKeyboardButton(
                        "Следующий",
                        callback_data=f'comments:'
                                      f'{post_id}:{current_comments + 1}')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text=parse_comment(comments[current_comments]),
                reply_markup=reply_markup
            )
    else:
        post_id = int(args[0])
        comments = get_comments(post_id)
        current_comments = 0
        keyboard = [
            [InlineKeyboardButton(
                "Следующий",
                callback_data=f'comments:'
                              f'{post_id}:{current_comments + 1}')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=chat.id,
            text=parse_comment(comments[current_comments]),
            reply_markup=reply_markup
        )


def get_comments(post_id):
    api_comment_url = (f'http://127.0.0.1:8000/'
                       f'api/v1/posts/{post_id}/comments')
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    try:
        comments = requests.get(
            api_comment_url,
            headers=headers,
        )
    except requests.exceptions.RequestException as e:
        logging.error('Ошибка соединения с сервером')
        raise e
    try:
        return comments.json()
    except json.decoder.JSONDecodeError as e:
        logging.error('Ошибка декодирования JSON')
        raise e


def parse_post(post):
    try:
        text = post['text']
    except KeyError:
        logging.error('Ошибка значения ключа')
        return 'Ошибка значения ключа'
    return text


def parse_comment(comment):
    try:
        comment_id = comment['text']
    except KeyError:
        logging.error('Ошибка значения ключа')
        return 'Ошибка значения ключа'
    return comment_id


def get_posts():
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    try:
        posts = requests.get(
            API_URL,
            headers=headers,
        )
    except requests.exceptions.RequestException as e:
        logging.error('Ошибка соединения с сервером')
        raise e
    try:
        return posts.json()
    except json.decoder.JSONDecodeError as e:
        logging.error('Ошибка декодирования JSON')
        raise e


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    try:
        updater = Updater(token=TELEGRAM_TOKEN)
        bot_client = Bot(token=TELEGRAM_TOKEN)
        updater.dispatcher.add_handler(CommandHandler(
            command="post_list",
            callback=send_post_list
        ))
        updater.dispatcher.add_handler(CommandHandler(
            command="post",
            callback=send_post,
            pass_args=True
        ))
        updater.dispatcher.add_handler(CallbackQueryHandler(main_handler))
        logging.info('Отправлено сообщение')
        updater.start_polling(poll_interval=2.0)
    except Exception as e:
        logging.error(f'Бот столкнулся с ошибкой: {e}')
        try:
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
        except telegram.error.Unauthorized:
            logging.error('Ошибка авторизации бота')
        except telegram.error.BadRequest:
            logging.error('Ошибка запроса телеграмм')
        time.sleep(5)


if __name__ == '__main__':
    main()
