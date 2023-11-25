import json

from telegram import InlineKeyboardButton


def get_origin_fail_keyboard(chat_id: int, reason: str = None, no_retry: bool = True):
    if no_retry:
        op = 'gtfnt'  # Get origin fail no retry
    else:
        op = 'gtf'  # Get origin fail
    if reason is None:
        reason = "获取原图出错！"
    return [
        [
            InlineKeyboardButton(
                text=reason,
                callback_data=json.dumps(
                    {
                        'op': op,
                        'cid': chat_id
                    }
                )
            )
        ],
    ]


def already_get_origin_keyboard():
    return [
        [
            InlineKeyboardButton(
                text='获取成功！',
                callback_data=json.dumps(
                    {
                        'op': 'agto'
                    }
                )
            )
        ]
    ]


def getting_origin_keyboard():
    return [
        [
            InlineKeyboardButton(
                text='正在获取原图……',
                callback_data=json.dumps(
                    {
                        'op': 'gito'
                    }
                )
            )
        ]
    ]


def timeout_keyboard():
    return [[
        InlineKeyboardButton(text='操作超时', callback_data=json.dumps({'op': 'timeout'}))
    ]]


def get_origin_keyboard(chat_id: int):
    return [
        [
            InlineKeyboardButton(
                text="获取原图",
                callback_data=json.dumps(
                    {
                        'op': "gto",  # get origin
                        'cid': chat_id
                    }
                )
            )
        ],
    ]
