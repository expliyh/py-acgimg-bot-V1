# 这是一个示例 Python 脚本。
import asyncio

import chat_stats
# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。

import database as db_class
from database import *
from pixiv import pixiv_api


def print_hi(name):
    # 在下面的代码行中使用断点来调试脚本。
    print(f'Hi, {name}')  # 按 Ctrl+F8 切换断点。


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    print_hi('PyCharm')
    database.create()
    db_class.create_table()
    debug_info = ImageInfo()
    debug_info.name = "debug"
    debug_info.link = "http://localhost/debug.png"
    debug_info.author = "debug_author"
    # debug_info.image_id = 114514
    debug_info.author_id = 1919810
    debug_info.caption = "JNTM"
    debug_info.filename = "debug.png"
    debug_info.helloimg_link = "debuglink"
    debug_info.original_url = "originurl"
    debug_info.sap_ori = False
    debug_info.pixiv_id = 1919810
    debug_info.raw_reply = "{sss}"
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(database.add_image_info(debug_info))

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
