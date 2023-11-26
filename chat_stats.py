import singleton_class_decorator

NORMAL = 0
IMAGE_ADD_REQUIRE_LINK = 1


@singleton_class_decorator.singleton
class ChatStats:
    def __init__(self):
        self.users = {}
        self.attachments = {}

    def set_stats(self, chat_id, stats):
        self.users[chat_id] = stats
        return

    def set_attachment(self, chat_id, attachment):
        self.attachments[chat_id] = attachment
        return

    def get_stats(self, chat_id) -> int:
        try:
            return self.users[chat_id]
        except KeyError:
            return NORMAL

    def get_attachment(self, chat_id):
        return self.attachments.get(chat_id)

    def clear(self, chat_id):
        try:
            self.users.pop(chat_id)
        except KeyError:
            pass
        try:
            self.attachments.pop(chat_id)
        except KeyError:
            pass
        return


chat_status = ChatStats()
