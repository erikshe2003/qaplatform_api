# -*- coding: utf-8 -*-

import os
import hashlib
import io
import datetime

from PIL import Image
from handler.config import appconfig
from handler.log import sys_logger


class SaveFile:
    # 根据传入的二进制文件以及账户邮箱地址，按照配置文件中的资源路径，保存为头像文件
    # default为0则保存默认头像，为1则保存指定头像
    # 存储格式：webp
    # 存储大小：32*32|64*64|128*128|256*256
    # 支持传入png|jpg|gif
    # gif只记录第一帧
    @classmethod
    def save_icon(cls, byte, mail, default):
        resource_path = appconfig.get("resource_path", "private")
        resource_path = resource_path if resource_path[-1] == "/" else resource_path + "/"
        mail = hashlib.md5(mail.encode('utf-8')).hexdigest()
        user_path = resource_path + mail
        # 根据配置文件中的路径，判断账户私有文件夹是否存在
        if os.path.exists(user_path) is False or os.path.isdir(user_path) is False:
            # 新建文件夹
            try:
                os.mkdir(user_path)
            except Exception as e:
                logmsg = "账户私有文件夹创建失败，失败原因：" + repr(e)
                sys_logger.error(logmsg)
        # 将图片转换为webp格式静态图片
        try:
            if default == 0:
                image = Image.open(appconfig.get("resource_path", "common") + "/icon.png")
            else:
                image = Image.open(io.BytesIO(byte))
        except Exception as e:
            logmsg = "账户头像byte数据PIL读取失败，失败原因：" + repr(e)
            sys_logger.error(logmsg)
        else:
            small = image.resize((32, 32), Image.ANTIALIAS)
            median = image.resize((64, 64), Image.ANTIALIAS)
            large = image.resize((128, 128), Image.ANTIALIAS)
            huge = image.resize((256, 256), Image.ANTIALIAS)
            try:
                small.save(user_path + "/icon_32_32.webp", "WEBP")
                median.save(user_path + "/icon_64_64.webp", "WEBP")
                large.save(user_path + "/icon_128_128.webp", "WEBP")
                huge.save(user_path + "/icon_256_256.webp", "WEBP")
            except Exception as e:
                logmsg = "账户头像创建失败，失败原因：" + repr(e)
                sys_logger.error(logmsg)
            else:
                image.close()
                small.close()
                median.close()
                large.close()
                huge.close()

    # 根据传入的新旧邮箱地址，修改私人文件夹名称
    @classmethod
    def move_dir(cls, old, new):
        resource_path = appconfig.get("resource_path", "private")
        resource_path = resource_path if resource_path[-1] == "/" else resource_path + "/"
        mail = hashlib.md5(old.encode('utf-8')).hexdigest()
        mail_path = resource_path + mail
        newmail = hashlib.md5(new.encode('utf-8')).hexdigest()
        new_mail_path = resource_path + newmail
        # 判断新文件夹是否存在，存在的话将其改名，名称需唯一
        if os.path.exists(new_mail_path) is True:
            try:
                os.rename(new_mail_path, new_mail_path + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
            except Exception as e:
                logmsg = "其他账户私有文件夹备份命名失败，失败原因：" + repr(e)
                sys_logger.error(logmsg)
        # 将旧文件夹名称修改为新的
        try:
            os.rename(mail_path, new_mail_path)
        except Exception as e:
            logmsg = "账户私有文件夹重命名失败，失败原因：" + repr(e)
            sys_logger.error(logmsg)
