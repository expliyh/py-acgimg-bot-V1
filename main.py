# 这是一个示例 Python 脚本。
import asyncio
import json

import chat_stats
# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。

import database as db_class
from database import *
from pixiv import pixiv_api
import image_bed


def print_hi(name):
    # 在下面的代码行中使用断点来调试脚本。
    print(f'Hi, {name}')  # 按 Ctrl+F8 切换断点。


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    print_hi('PyCharm')
    database.create()
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(pixiv_api.get_raw(112900318))
    print(json.dumps(pool))

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
