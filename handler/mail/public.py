# -*- coding: utf-8 -*-

import smtplib

from urllib import parse
from email.header import Header
from email.mime.text import MIMEText
from handler.log import sys_logger
from handler.config import appconfig


# 公共邮件发送器
class PublicMailer:
    # 初始化
    # 需传入邮箱地址/邮箱密码/SMTP服务器地址/SMTP服务器端口号/SMTP端口的SSL状态位
    def __init__(self, address, password, smtp_host, smtp_port, smtp_ssl):
        # 检查传参合法性
        # address
        if type(address) is str:
            self.send_address = address
        else:
            raise TypeError("公共邮箱地址填写非法")
        # password
        if type(password) is str:
            self.send_password = password
        else:
            raise TypeError("公共邮箱密码填写非法")
        # smtp_host
        if type(smtp_host) is str:
            self.smtp_host = smtp_host
        else:
            raise TypeError("SMTP服务器地址填写非法")
        # smtp_port
        if type(smtp_port) is int:
            self.smtp_port = smtp_port
        else:
            raise TypeError("SMTP服务器端口填写非法")
        # smtp_ssl
        if type(smtp_ssl) is bool:
            self.smtp_ssl = smtp_ssl
        else:
            raise TypeError("SMTP服务器端口SSL指定不明")

    # 发送重置密码邮件
    # 需传入收件人地址/校验码
    def sendmail_reset_password(self, user_id, to, code, operationid):
        # 检查传参合法性
        # to
        if type(to) is str and type(code) is str:
            logmsg = "准备给" + to + "发送重置密码邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试重置密码：
                                    <a href="%s?userId=%s&mail=%s&code=%s&operate=%s">点我打开重置密码页</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                        to.split("@")[0],
                        appconfig.get("web", "http") + "://" +
                        appconfig.get("web", "host") + ":" +
                        appconfig.get("web", "port") + appconfig.get("web_url", "resetPassword"),
                        str(user_id),
                        parse.quote(to),
                        parse.quote(code),
                        str(operationid),
                        appconfig.get('org', 'abbreviation'),
                    )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(to, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            self.__send(to, msg)
            logmsg = "给" + to + "发送重置密码邮件结束"
            sys_logger.info(logmsg)
            return True
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
            return False

    # 发送账号注册申请邮件
    # 需传入收件人地址/校验码
    def sendmail_register(self, user_id, to, code, operationid):
        # 检查传参合法性
        # to
        if type(to) is str and type(code) is str:
            logmsg = "准备给" + to + "发送账号注册申请邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试注册账号：
                                    <a href="%s?userId=%s&mail=%s&code=%s&operate=%s">点我打开注册账号页</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                to.split("@")[0],
                appconfig.get("web", "http") + "://" +
                appconfig.get("web", "host") + ":" +
                appconfig.get("web", "port") + appconfig.get("web_url", "infoConfirm"),
                str(user_id),
                parse.quote(to),
                parse.quote(code),
                str(operationid),
                appconfig.get('org', 'abbreviation'),
            )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(to, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            result_flag, result_type = self.__send(to, msg)
            logmsg = "给" + to + "发送账号注册邮件结束"
            sys_logger.info(logmsg)
            return result_flag, result_type
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
            return False, -1

    # 发送修改绑定邮箱申请邮件
    # 需传入新邮箱收件人地址/校验码
    def sendmail_change_mail(self, old, new, code, operationid):
        # 检查传参合法性
        # to
        if type(new) is str and type(code) is str:
            logmsg = "准备给" + old + "发送更换绑定邮箱申请邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试修改绑定邮箱：
                                    <a href="%s?mail=%s&newmail=%s&code=%s&operate=%s">点我打开绑定邮箱修改页</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                old.split("@")[0],
                appconfig.get("web", "http") + "://" +
                appconfig.get("web", "host") + ":" +
                appconfig.get("web", "port") + appconfig.get("web_url", "changeMail"),
                parse.quote(old),
                parse.quote(new),
                parse.quote(code),
                str(operationid),
                appconfig.get('org', 'abbreviation'),
            )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(new, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            result_flag, result_type = self.__send(new, msg)
            logmsg = "给" + new + "发送来自" + old + "的修改绑定邮箱申请邮件结束"
            sys_logger.info(logmsg)
            return result_flag, result_type
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
        return False, -1

    # 发送重置密码成功邮件
    # 需传入收件人地址/校验码
    def sendmail_reset_password_success(self, to):
        # 检查传参合法性
        # to
        if type(to) is str:
            logmsg = "准备给" + to + "发送重置密码成功邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试重置密码：
                                    <a href="%s">重置密码成功</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                to.split("@")[0],
                appconfig.get("web", "http") + "://" +
                appconfig.get("web", "host") + ":" +
                appconfig.get("web", "port") + appconfig.get("web_url", "login"),
                appconfig.get('org', 'abbreviation'),
            )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(to, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            result_flag, result_type = self.__send(to, msg)
            logmsg = "给" + to + "发送重置密码成功邮件结束"
            sys_logger.info(logmsg)
            return result_flag, result_type
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
            return False, -1

    # 发送账户新增成功邮件
    # 需传入收件人地址
    def sendmail_register_success(self, to):
        # 检查传参合法性
        # to
        if type(to) is str:
            logmsg = "准备给" + to + "发送账户注册成功邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试注册账号：
                                    <a href="%s">注册账号成功</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                to.split("@")[0],
                appconfig.get("web", "http") + "://" +
                appconfig.get("web", "host") + ":" +
                appconfig.get("web", "port") + appconfig.get("web_url", "login"),
                appconfig.get('org', 'abbreviation'),
            )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(to, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            result_flag, result_type = self.__send(to, msg)
            logmsg = "给" + to + "发送注册账号成功邮件结束"
            sys_logger.info(logmsg)
            return result_flag, result_type
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
            return False, -1

    # 发送账户邮箱修改成功邮件
    # 需传入收件人地址
    def sendmail_changemail_success(self, to):
        # 检查传参合法性
        # to
        if type(to) is str:
            logmsg = "准备给" + to + "发送账户绑定邮箱修改成功邮件"
            sys_logger.info(logmsg)
            # 编辑邮件具体内容
            mail_msg = """
                <html>
                    <head>
                        <style type="text/css">
                            #platform_logo {
                                height: 18px;
                            }
                            #platform_logo_left{
                                transition: all 0.5s;
                                fill: #4DB6FF;
                            }
                            #platform_logo_center{
                                transition: all 0.5s;
                                fill: #539D2C;
                            }
                            #platform_logo_right{
                                transition: all 0.5s;
                                fill: #EDA833;
                            }
                            #platform_logo > path:hover{
                                transition: all 0.5s;
                                fill: lightgrey;
                            }
                        </style>
                    </head>
                    <body style="margin:0;">
                        <div style="background-color: #f5f5f5;">
                            <div style="margin-left: 20px;padding-top: 10px;
                            padding-bottom: 10px;font-size: 18px;font-weight: 600;">
                                Dear %s,
                            </div>
                            <div style="position: relative;margin-left: 20px;margin-right: 20px;
                            font-size: 15px;background-color: white;border: 1px solid darkgrey;border-radius: 4px;">
                                <div style="margin-top: 15px;margin-left: 15px;padding-bottom: 10px;">
                                    您正在尝试修改绑定邮箱：
                                    <a href="%s">绑定邮箱修改成功</a>
                                    <div style="margin-left: 10px;padding-bottom: 10px;font-size: 16px;"></div>
                                </div>
                            </div>
                            <div style="margin-top: 10px;padding-bottom: 10px;
                            color: darkgrey;text-align: right;">
                                <div style="margin-right: 20px;font-size: 12px;">
                                    本条消息发送自%s测试平台
                                </div>
                            </div>
                        </div>
                    </body>
                </html>
                """ % (
                to.split("@")[0],
                appconfig.get("web", "http") + "://" +
                appconfig.get("web", "host") + ":" +
                appconfig.get("web", "port") + appconfig.get("web_url", "login"),
                appconfig.get('org', 'abbreviation'),
            )
            # 装载消息
            # 添加根MIME
            msg = MIMEText(mail_msg, 'html', 'utf-8')
            # 初始化邮件发送人
            msg['From'] = Header(self.send_address, 'utf-8')
            # 初始化邮件接收人
            msg['To'] = Header(to, 'utf-8')
            # 初始化邮件主题
            msg['Subject'] = Header(
                '%s测试平台-账号注册' % appconfig.get('org', 'abbreviation'),
                'utf-8'
            )
            # 发送
            result_flag, result_type = self.__send(to, msg)
            logmsg = "给" + to + "发送绑定邮箱修改成功邮件结束"
            sys_logger.info(logmsg)
            return result_flag, result_type
        else:
            logmsg = "接收邮件地址或校验码填写非法"
            sys_logger.error(logmsg)
            return False, -1

    # 连接SMTP服务器并发送邮件
    def __send(self, to, msg):
        error_flag = True
        # -1 接收邮件地址或校验码填写非法
        # 0 公共邮件发送成功
        # 1 SMTP服务器连接失败
        # 2 公共邮箱登陆失败
        # 3 公共邮件发送失败
        error_type = 0
        logmsg = "准备发送邮件"
        sys_logger.info(logmsg)
        # 尝试连接服务器
        try:
            # 根据SMTP服务器SSL状态连接
            if self.smtp_ssl is True:
                smtp_server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            # 打印日志
            logmsg = "SMTP服务器连接成功"
            sys_logger.debug(logmsg)
        except Exception as A:
            logmsg = "SMTP服务器连接失败,失败信息:" + repr(A)
            error_flag = False
            error_type = 1
            sys_logger.error(logmsg)
        else:
            try:
                smtp_server.login(self.send_address, self.send_password)
                logmsg = "公共邮件箱登陆成功"
                sys_logger.debug(logmsg)
            except Exception as B:
                logmsg = "公共邮件箱登陆失败,失败信息:" + repr(B)
                error_flag = False
                error_type = 2
                sys_logger.error(logmsg)
            else:
                try:
                    smtp_server.sendmail(self.send_address, to, msg.as_string())
                    smtp_server.quit()
                    logmsg = "公共邮件发送成功"
                    sys_logger.debug(logmsg)
                except Exception as C:
                    logmsg = "公共邮件发送失败,失败信息:" + repr(C)
                    error_flag = False
                    error_type = 3
                    sys_logger.warn(logmsg)
        logmsg = "邮件发送结束"
        sys_logger.info(logmsg)
        return error_flag, error_type
