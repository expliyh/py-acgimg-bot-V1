import unittest

from chat_stats import CONFIG_IMAGE_BED_SET, IMAGE_ADD_REQUIRE_LINK, NORMAL, ChatStats


class ChatStatsTestCase(unittest.TestCase):
    def setUp(self):
        self.chat_stats = ChatStats()
        self.chat_ids = (1001, 1002)
        for chat_id in self.chat_ids:
            self.chat_stats.clear(chat_id)

    def tearDown(self):
        for chat_id in self.chat_ids:
            self.chat_stats.clear(chat_id)

    def test_unknown_chat_uses_normal_state(self):
        self.assertEqual(NORMAL, self.chat_stats.get_stats(self.chat_ids[0]))
        self.assertIsNone(self.chat_stats.get_attachment(self.chat_ids[0]))

    def test_state_and_attachment_are_stored_per_chat(self):
        self.chat_stats.set_stats(self.chat_ids[0], IMAGE_ADD_REQUIRE_LINK)
        self.chat_stats.set_stats(self.chat_ids[1], CONFIG_IMAGE_BED_SET)
        self.chat_stats.set_attachment(self.chat_ids[0], {"image_id": 42})

        self.assertEqual(
            IMAGE_ADD_REQUIRE_LINK,
            self.chat_stats.get_stats(self.chat_ids[0]),
        )
        self.assertEqual(
            CONFIG_IMAGE_BED_SET,
            self.chat_stats.get_stats(self.chat_ids[1]),
        )
        self.assertEqual(
            {"image_id": 42},
            self.chat_stats.get_attachment(self.chat_ids[0]),
        )
        self.assertIsNone(self.chat_stats.get_attachment(self.chat_ids[1]))

    def test_clear_removes_state_and_attachment(self):
        chat_id = self.chat_ids[0]
        self.chat_stats.set_stats(chat_id, IMAGE_ADD_REQUIRE_LINK)
        self.chat_stats.set_attachment(chat_id, "pending image")

        self.chat_stats.clear(chat_id)

        self.assertEqual(NORMAL, self.chat_stats.get_stats(chat_id))
        self.assertIsNone(self.chat_stats.get_attachment(chat_id))


if __name__ == "__main__":
    unittest.main()
