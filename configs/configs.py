from singleton_class_decorator import singleton


@singleton
class Configs:
    dict_configs: dict

    def get_config(self, what: str):
        pass

    def __init__(self):
        pass


configs = Configs()
