class ImageQueue:
    def __init__(self, chat_id: int, message_id: int, image_id: int, pending: bool, downloaded: bool):
        self.chat_id: int = chat_id
        self.message_id: int = message_id
        self.image_id: int = image_id
        self.pending: bool = pending
        self.downloaded: bool = downloaded
