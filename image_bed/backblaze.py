from datetime import datetime

from singleton_class_decorator import singleton

from configs import configs, BackblazeConfig
from b2sdk.v2 import InMemoryAccountInfo, B2Api, FileVersion, Bucket


@singleton
class Backblaze:
    def upload_image(self, file_name: str, document: bytes) -> str:
        # self.b2_api.authorize_automatically()
        self.auth()
        info = {
            "msg": "Automatic upload by py-acgimg-bot"
        }
        time = datetime.now()
        path = f"{time.year}/{time.month:02d}/{time.day:02d}/"
        file_version: FileVersion = self.bucket.upload_bytes(
            data_bytes=document,
            file_name=self.base_path + path + file_name,
            file_info=info
        )
        url = self.conf_cache.access_url_base + self.conf_cache.base_path + path + file_name
        return url

    def __init__(self, conf: BackblazeConfig):
        self.info = InMemoryAccountInfo()
        self.b2_api = B2Api(self.info)
        self.bucket: Bucket | None = None
        self.base_path = conf.base_path
        self.conf_cache = conf

    def auth(self):
        if self.b2_api.authorize_automatically():
            return
        elif self.conf_cache.access_url_base is None or self.conf_cache.base_path is None or self.conf_cache.bucket_name is None:
            return
        else:
            self.b2_api.authorize_account(
                "production",
                application_key_id=self.conf_cache.application_key_id,
                application_key=self.conf_cache.application_key
            )
            if self.bucket is None:
                self.bucket = self.b2_api.get_bucket_by_name(self.conf_cache.bucket_name)
