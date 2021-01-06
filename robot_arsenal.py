import json
from urllib import request, parse


class RobotArsenal:
    def __init__(self, app_id, app_secret):
        '''
        飞书机器人武器库
        '''
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = self.__get_tenant_access_token()

    def __get_tenant_access_token(self, ):
        """
        获取access token，获取的不是data，不封装
        """
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {
            "Content-Type": "application/json"
        }
        req_body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data,
                              headers=headers, method='POST')
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return ""

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("get tenant_access_token error, code =", code)
            return ""
        return rsp_dict.get("tenant_access_token", "")

    def __request(self, url: str, headers: dict, req_body: dict, method='POST') -> dict:
        """
        封装发送请求逻辑，返回response.data
        """
        if headers == None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.tenant_access_token
            }

        if req_body == None:
            req_body = {}

        data = bytes(json.dumps(req_body), encoding='utf8')
        req = request.Request(url=url, data=data,
                              headers=headers, method=method)
        try:
            response = request.urlopen(req)
        except Exception as e:
            print(e.read().decode())
            return {}

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        code = rsp_dict.get("code", -1)
        if code != 0:
            print("[RobotArsenal.__request] error, code =", code)
            return {}
        return rsp_dict.get("data", {})

    def __send_message(self, message: str, id_type:str, id: str):
        """
        发送消息
        :param message: 文本消息
        :param id_type: id类型 user_id / open_id / chat_id
        :param id: 对应id
        """
        url = "https://open.feishu.cn/open-apis/message/v4/send/"
        req_body = {
            id_type: id,
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        data = self.__request(url, None, req_body)
        message_id = data.get("message_id", "")
        if message_id != "":
            print('[RobotArsenal.__send_message] 消息发送成功，message_id={0}'.format(message_id))

    def __get_chat_list(self, ) -> list:
        """
        获取机器人所在群组的关键信息列表 [(chat_id, name), ]
        """
        url = "https://open.feishu.cn/open-apis/chat/v4/list"
        data = self.__request(url, None, None, 'GET')
        group_list = data.get("groups", [])
        ret = []
        # 可获取信息如下
        # "avatar", "chat_id", "description", "name", "owner_open_id", "owner_user_id":
        for group in group_list:
            ret.append((group['chat_id'], group['name']))
        return ret

    def __get_chat_id_with_name(self, chat_name) -> str:
        """
        :param chat_name: 群聊名
        根据群聊名获取chat_id
        """
        ret = ""
        chat_list = self.__get_chat_list()
        for chat_info in chat_list:
            if chat_info[1] == chat_name:
                ret = chat_info[0]
        return ret

    def __get_user_id_with_name(self, username):
        """
        :param username: 用户名
        根据用户名获取user_id
        """
        url = "https://open.feishu.cn/open-apis/search/v1/user?query={0}".format(username)
        data = self.__request(url, None, None, 'GET')
        
        user_list = data.get("users", [])
        ret = ""
        for user_dict in user_list:
            if user_dict["name"] == username:
                ret = user_dict["user_id"]
        return ret

    def __get_members_in_chat(self, chat_id: str) -> list:
        """
        获取群组中的关键用户信息列表 [{'open_id':,'user_id':}...]
        """
        url = "https://open.feishu.cn/open-apis/chat/v4/info?chat_id={0}".format(chat_id)
        data = self.__request(url, None, None, 'GET')
        members = data.get("members")
        return members

    def send_message_to_chat(self, message: str, chat_name: str):
        """
        将消息发送到群聊
        :param message: 需要发送的消息
        :param chat_name: 群聊名
        """
        chat_id = self.__get_chat_id_with_name(chat_name)
        if chat_id != "":
            self.__send_message(message, "chat_id", chat_id)
        else:
            print("[RobotArsenal.send_message_to_chat] 未找到群聊\"{0}\"".format(chat_name))

    def send_message_to_user(self, message: str, username: str):
        """
        [不可用]将消息私聊发送给用户
        :param message: 需要发送的消息
        :param username: 用户名
        """
        user_id = self.__get_user_id_with_name(username)
        if user_id != "":
            self.__send_message(message, "user_id", user_id)
        else:
            print("[RobotArsenal.send_message_to_chat] 未找到用户\"{0}\"".format(username))

    def send_message_to_user_with_id(self, message, user_id):
        """
        发送私聊消息给用户
        :param message: 需要发送的消息
        :param user_id: 用户id
        """
        self.__send_message(message, "user_id", user_id)

    def get_members_in_chat(self, chat_name):
        """
        获取群聊中所有用户信息
        :param chat_name: 群聊名
        """
        chat_id = self.__get_chat_id_with_name(chat_name)
        members = self.__get_members_in_chat(chat_id)
        return members
