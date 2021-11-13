# coding: utf-8

import os
import sys
import time
import smtplib
import socks
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MAIL_CFG = 'mail-cfg.txt'

def loadMailCfg():
    cfg = {}
    with open(MAIL_CFG, 'r', encoding='utf-8') as f:
        for line in f:
            k, v = line.strip().split(':', 1)
            cfg[k] = v
    return cfg


cfg = loadMailCfg()

proxy_server = cfg['proxy_server']
proxy_port = int(cfg['proxy_port'])
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_server, proxy_port)
socks.wrapmodule(smtplib)

def genMail():
    mail_title = cfg['mail_title']
    incoming = cfg['incoming']
    reports = []
    count = 0
    for root, dirs, names in os.walk(incoming):
        for name in names:
            if name.endswith('.txt'):
                path = os.path.join(root, name)
                count += 1
                with open(path, 'rb') as f:
                    reports.append(f.read().decode('utf-8'))

    mail_title = '%s [%s] [%d]' % (mail_title, time.strftime('%Y-%m-%d'), count)
    mail_body = '\n\n'.join(reports)
    return mail_title, mail_body


def sendMail(mail_title, mail_body):
    mail_host = cfg['smtp']
    mail_user = cfg['user']
    mail_pass = cfg['pass']
    sender    = cfg['sender']
    mail_to   = cfg['send_to']
    receivers = [mail_to, sender]

    message = MIMEMultipart('alternative')
    message['Subject'] = mail_title
    message['From'] = sender
    message['To'] = receivers[0]
    message['Cc'] = sender

    body = MIMEText(mail_body, 'plain')
    message.attach(body)

    # print(message.as_string())

    #登录并发送邮件
    try:
        smtpObj = smtplib.SMTP(mail_host, port=587)
        smtpObj.starttls()
        #登录到服务器
        smtpObj.login(mail_user, mail_pass)
        #发送
        smtpObj.sendmail(sender, receivers, message.as_string())
        #退出
        smtpObj.quit()
        print('sendMail: success')
    except smtplib.SMTPException as e:
        print('sendMail: error',e) #打印错误


def main():
    mail_title, mail_body = genMail()
    sendMail(mail_title, mail_body)

if __name__ == '__main__':
    main()

