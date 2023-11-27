import os

from dotenv import load_dotenv

__env_path = '.env'


class __Config:
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv('DATABASE_HOST')
        self.db_port = int(os.getenv('DATABASE_PORT'))
        self.db_username = os.getenv('DATABASE_USERNAME')
        self.db_password = os.getenv('DATABASE_PASSWORD')
        self.db_name = os.getenv('DATABASE_NAME')
        self.db_prefix = os.getenv('DATABASE_PREFIX')
        self.py_api_url = os.getenv('PIXIV_API_URL')
        self.pixiv_token = os.getenv('PIXIV_TOKEN')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.developer_chat_id = os.getenv('DEVELOPER_CHAT_ID')


config = __Config()
