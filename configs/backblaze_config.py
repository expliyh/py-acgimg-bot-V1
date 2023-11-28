from .base_config import BaseConfig


class BackblazeConfig(BaseConfig):

    def __init__(self, application_key_id: str = None, application_key: str = None, bucket_name: str = None,
                 access_url_base: str = None):
        super()
        self.description = 'BackBlaze'
        self.what = 'img_bed'
        self.application_key_id = application_key_id
        self.application_key = application_key
        self.bucket_name = bucket_name
        self.base_path = "bot-images/"
        self.access_url_base = access_url_base
        if self.access_url_base is not None:
            if access_url_base[-1] != '/':
                self.access_url_base += '/'

    def get_conf_brief(self):
        ans = ""
        if self.application_key_id is not None:
            ans += f"app_key_id: {self.application_key_id}\n"
        else:
            ans += f"app_key_id: 未配置\n"
        if self.application_key is not None:
            ans += f"app_key: {self.application_key[0:5]}**********{self.application_key[-5:-1]}\n"
        else:
            ans += f"app_key: 未配置\n"
        if self.bucket_name is not None:
            ans += f"存储桶名称: {self.bucket_name}\n"
        else:
            ans += f"存储桶名称: 未配置\n"
        if self.base_path is not None:
            ans += f"存储路径: {self.base_path}\n"
        else:
            ans += f"存储路径: 未配置\n"
        if self.access_url_base is not None:
            ans += f"公网访问链接: {self.access_url_base}\n"
        else:
            ans += f"公网访问链接: 未配置\n"
        return ans


description: str
what: str
application_key_id: str
application_key: str
bucket_name: str
base_path: str
access_url_base: str
