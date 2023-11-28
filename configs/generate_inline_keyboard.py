import json

from telegram import InlineKeyboardButton


def config_img_bed_change_keyboard(page: int = 0):
    return [
        [
            InlineKeyboardButton(
                text='返回',
                callback_data=f"config:image_bed"
            )
        ],
        [
            InlineKeyboardButton(
                text='取消图床自动化',
                callback_data=f"config:image_bed:cancel"
            )
        ],
        [
            InlineKeyboardButton(
                text='BackBlaze',
                callback_data=f"config:image_bed:set:backblaze"
            )
        ]
    ]


def config_img_bed_none_edit_keyboard(page: int = 0):
    return [
        [
            InlineKeyboardButton(
                text='更换图床',
                callback_data=f"config:image_bed:change"
            ),
            InlineKeyboardButton(
                text='返回',
                callback_data= f"config:image_bed"
            )
        ]
    ]


def config_img_bed_backblaze_edit_keyboard(page: int = 0):
    return [
        [
            InlineKeyboardButton(
                text='更换图床',
                callback_data=f"config:image_bed:change"
            ),
            # InlineKeyboardButton(
            #     text='返回',
            #     callback_data=f"config:image_bed"
            # )
        ],
        [
            InlineKeyboardButton(
                text='APP_KEY_ID',
                callback_data=f"config:image_bed:edit:app_key_id"
            ),
            InlineKeyboardButton(
                text='APP_KEY',
                callback_data= f"config:image_bed:edit:app_key"
            )
        ],
        [
            InlineKeyboardButton(
                text='存储桶名称',
                callback_data=f"config:image_bed:edit:bucket_name"
            ),
            InlineKeyboardButton(
                text='存储路径',
                callback_data=f"config:image_bed:edit:base_path"
            )
        ],
        [
            InlineKeyboardButton(
                text='公网链接',
                callback_data=f"config:image_bed:edit:access_url"
            ),
            InlineKeyboardButton(
                text='Invalid',
                callback_data=json.dumps(
                    {
                        'op': f"empty"
                    }
                )
            )
        ]
    ]


def config_main_menu_keyboard(page: int = 0):
    return [
        [
            InlineKeyboardButton(
                text='图床配置',
                callback_data=f"config:image_bed"
            )
        ]
    ]

