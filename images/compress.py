from PIL import Image
import os
from database import ImageInfo
from .get_info import get_size, __path


def compress_image_to_target_size(img_path, out_path, target_size=5000, step=5, quality=95):
    """压缩图像到指定体积
    :param img_path: 压缩图像读取地址
    :param out_path: 压缩图像存储地址
    :param target_size: 压缩目标，KB
    :param step: 每次调整的压缩比率
    :param quality: 初始压缩比率
    :return: 压缩文件地址，压缩文件大小
    """
    o_size = get_size(img_path)
    if o_size < target_size:
        return Image.open(img_path)

    img = Image.open(img_path)

    while o_size > target_size:
        img = Image.open(img_path)
        img = img.convert('RGB')
        img.save(out_path, quality=quality)
        if quality - step < 0:
            break
        quality -= step
        o_size = get_size(out_path)

    # print('File size: ' + str(o_size))
    img.close()
    return


def auto_compress_for_telegram_photo(img_path, image_id: int, sub_id: int):
    """
    将图像压缩为Telegram可发送图片大小，保存在__path/compressed_<image_id>.jpg
    :param img_path: 输入图片的路径
    :param image_id: 图片ID
    :return:
    """
    out_path = f"{__path}compressed_{str(image_id)}_{str(sub_id)}.jpg"
    compress_image_to_target_size(img_path, out_path, 9000)
    return
