#!/usr/bin/env python
# --coding:utf-8--

from http.server import BaseHTTPRequestHandler, HTTPServer
from os import path
import time
import traceback
import json
from service import Service
from urllib import request, parse
from robot_arsenal import RobotArsenal


APP_ID = "cli_9f58afd2fa2b900c"
APP_SECRET = "84Pb4n70TjT77dsN9VbxJdgtQkrRkJEC"
APP_VERIFICATION_TOKEN = "0r5T8WDJl5nxZFZ901xWJfCSgfhN0f7r"
UNKNOWN_DEFAULT = 'UNKNOWN'

# 机器人启动消息会被发送给这个id对应的用户
NOTIFY_USER_ID = 'a86adbec'
NOTIFY_START_MESSAGE = '[{0}] ROBOT SERVICE START'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

request_interests = ['chat_type', 'open_id', 'open_chat_id', 'msg_type', 'type', 'text']

bot = RobotArsenal(APP_ID, APP_SECRET)
service = Service(bot)

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 解析请求 body
        req_body = self.rfile.read(int(self.headers['content-length']))
        obj = json.loads(req_body.decode("utf-8"))

        # 校验 verification token 是否匹配，token 不匹配说明该回调并非来自开发平台
        token = obj.get("token", "")
        if token != APP_VERIFICATION_TOKEN:
            print("verification token not match, token =", token)
            self.response("")
            return

        # 根据 type 处理不同类型事件
        type = obj.get("type", "")
        event = obj.get("event", "")
        self.print_request_detail_message(type, event) 

        if "url_verification" == type:  # 验证请求 URL 是否有效
            self.handle_request_url_verify(obj)
        elif "event_callback" == type:  # 事件回调
            # 获取事件内容和类型，并进行相应处理，此处只关注给机器人推送的消息事件
            if event.get("type", "") == "message":
                self.handle_message(event)
                return
        return

    def print_request_detail_message(self, type_str, event_body):
        print('---------- INCOMING REQUEST ----------')
        print('[request type] ' + type_str)
        for interest in request_interests:
            print('[{0}] {1}'.format(interest, event_body.get(interest, UNKNOWN_DEFAULT)))
        return

    def handle_request_url_verify(self, post_obj):
        # 原样返回 challenge 字段内容
        challenge = post_obj.get("challenge", "")
        rsp = {'challenge': challenge}
        self.response(json.dumps(rsp))
        return

    def handle_message(self, event):
        # 此处只处理 text 类型消息，其他类型消息忽略
        msg_type = event.get("msg_type", "")
        if msg_type == "sticker":
            print("[EchoBot] 记录表情包file_key {0}".format(event.get("file_key")))
            self.response("")
            return

        if msg_type != "text":
            print("unknown msg_type =", msg_type)
            self.response("")
            return

        # 通知服务中心进行对应服务处理
        if event.get("text") != event.get("text_without_at_bot"):
            # service.message_broadcast(event.get("chat_type"), event.get("open_id"), event.get("open_chat_id"), event.get("text"))
            service.process_message_service(event)
        
        self.response("")
        return

    def response(self, body):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body.encode())

    def get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type" : "application/json"
        }
        req_body = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            raise

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("get tenant_access_token error, code =", code)
            return ""
        return rsp_dict.get("tenant_access_token", "")

    def send_message(self, token, open_id, text):
        url = "https://open.feishu.cn/open-apis/message/v4/send/"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        req_body = {
            "open_id": open_id,
            "msg_type": "text",
            "content": {
                "text": text
            }
        }

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            raise

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        print('---------- RESPONSE ----------')
        print(rsp_dict)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("send message error, code = ", code, ", msg =", rsp_dict.get("msg", ""))

def run():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print("[echo_bot] start.....")
    bot.send_message_to_user_with_userid(NOTIFY_START_MESSAGE, NOTIFY_USER_ID)
    httpd.serve_forever()

if __name__ == '__main__':
    try:
        run()
    except BaseException as e:
        bot.send_message_to_user_with_userid(traceback.format_exc(), NOTIFY_USER_ID)
        bot.send_message_to_user_with_userid('[{0}] ROBOT SERVICE TERMINATED'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), NOTIFY_USER_ID)
