# coding: utf-8

import os
import sys
import time
import smtplib
import base64
import socket
import socks as sockswrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from httplib2 import socks

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


MAIL_CFG = 'mail-cfg.txt'

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

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

sockswrap.setdefaultproxy(sockswrap.PROXY_TYPE_SOCKS5, proxy_server, proxy_port)
sockswrap.wrapmodule(smtplib)

socket.socket = socks.socksocket
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_server, proxy_port)

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


def getGoogleCreds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def gmailSendMessage(mail_title, mail_body):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    mail_host = cfg['smtp']
    mail_user = cfg['user']
    mail_pass = cfg['pass']
    sender    = cfg['sender']
    mail_to   = cfg['send_to']

    # creds, _ = google.auth.default()
    creds = getGoogleCreds()

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEText(mail_body)
        message['To'] = mail_to
        message['From'] = mail_user
        message['Subject'] = mail_title
        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'raw': encoded_message
        }
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message

def main():
    mail_title, mail_body = genMail()
    # sendMail(mail_title, mail_body)
    gmailSendMessage(mail_title, mail_body)

if __name__ == '__main__':
    main()

