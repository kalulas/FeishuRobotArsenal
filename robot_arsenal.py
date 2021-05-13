import re
import time
import json
from urllib import request, parse

# 匹配富文本@成员
at_pattern = r"@(\w+)\s"
at_all_pattern = "所有人"
at_format_output = "<at open_id=\"{0}\"></at> "
at_all_replace = "all"

# 匹配富文本超链接成员
url_pattern = r'(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]\s'
# 匹配富文本普通文本成员
common_text_pattern = r'[\s]*[^\s\@]+[\s]*'
# 需要从普通文本中删减的部分
strip_pattern = r''

class RobotArsenal:
    def __init__(self, app_id, app_secret):
        '''
        飞书机器人武器库
        '''
        print("[RobotArsenal] created with ID:{0} SECRET:{1}".format(app_id, app_secret))
        
        self.app_id = app_id
        self.app_secret = app_secret
        # {用户名 -> {'user_id':, 'open_id':, 'union_id':}, }
        self.name_to_id_dict = {}
        self.__update_access_token()
        # 提前缓存用户信息
        self.__update_department_members()

    def __update_access_token(self, ):
        """
        tenant access token 每隔2小时过期，需要定时刷新
        """
        self.access_token = self.__get_tenant_access_token()
        print("[RobotArsenal.__update_access_token][{0}] update robot's access token to {1}".format(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.access_token))

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

    def __handle_error_code(self, code: int):
        print('[RobotArsenal.__handle_error_code] 处理错误码{0}'.format(code))
        if code == 99991663:
            print('[RobotArsenal.__handle_error_code] 重新获取access_token')
            self.__update_access_token()
        print('[RobotArsenal.__handle_error_code] 未被处理的错误码{0}'.format(code))

    def __request(self, url: str, headers: dict, req_body: dict, method='POST') -> dict:
        """
        封装发送请求逻辑，返回response.data
        """
        default_headers = {
            "Content-Type": "application/json", 
            "Authorization": "Bearer " + self.access_token, 
        }
        print("[RobotArsenal.__request] url:{0}, headers:{1}, req_body:{2}, method:{3}".format(url, 
        str(headers or default_headers), str(req_body or {}), method))

        data = bytes(json.dumps(req_body or {}), encoding='utf8')
        req = request.Request(url=url, data=data, headers=headers or default_headers, method=method)
        try:
            response = request.urlopen(req)
        except Exception as e:
            print("[RobotArsenal.__request] Exception happened during request.urlopen(req)")
            rsp_body = e.read().decode()
            rsp_dict = json.loads(rsp_body)
            code = rsp_dict.get("code", -1)
            if code != 0:
                print("[RobotArsenal.__request] error, code =", code)
                self.__handle_error_code(code)
                return self.__request(url, headers, req_body, method)

        rsp_body = response.read().decode('utf-8')
        rsp_dict = json.loads(rsp_body)
        return rsp_dict.get("data", {})

    def __send_message(self, message: str, id_type: str, id: str):
        """
        发送消息
        :param message: 文本消息
        :param id_type: id类型 user_id / open_id / chat_id
        :param id: 对应id
        """
        message = self.__preprocess_message(message)
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

    def __send_rich_message(self, rich_message: dict, id_type: str, id: str):
        """
        发送富文本消息
        TODO 注释补全
        """
        url = "https://open.feishu.cn/open-apis/message/v4/send/"
        req_body = {
            id_type: id,
            "msg_type": "post",
            "content": {
                "post": rich_message
            }
        }
        # print(str(req_body))
        data = self.__request(url, None, req_body)
        message_id = data.get("message_id", "")
        if message_id != "":
            print('[RobotArsenal.__send_message] 消息发送成功，message_id={0}'.format(message_id))

    def __get_robot_authed_departments(self) -> list:
        """
        查询机器人所在的授权部门open_id列表
        """
        url = "https://open.feishu.cn/open-apis/contact/v1/scope/get"
        data = self.__request(url, None, None, "GET")
        return data.get("authed_open_departments", [])

    def __get_department_members_with_id(self, department_open_id: str) -> list:
        """
        :param department_open_id: 部门open_id
        获取机器人所在部门的用户列表
        """
        url = "https://open.feishu.cn/open-apis/contact/v1/department/user/list?open_department_id={0}&page_size=100&fetch_child=true".format(
            department_open_id)

        members = []
        data = self.__request(url, None, None, "GET")
        members = data.get("user_list", [])

        while data.get("has_more", False):
            page_token = data.get("page_token")
            data = self.__request(url + "&page_token=" + page_token, None, None, "GET")
            members = members + data.get("user_list", [])
        
        return members

    def __update_department_members(self):
        """
        获取机器人归属部门的用户信息存入到name_to_id_list
        """
        open_departments = self.__get_robot_authed_departments()
        if len(open_departments) == 0:
            print("[RobotArsenal.get_members_infor_pair_in_chat] 机器人不归属于任何一个部门")
            return
        
        members = []

        for deparment_open_id in open_departments:
            result = self.__get_department_members_with_id(deparment_open_id)
            members = members + result
        
        self.name_to_id_dict.clear()
        for member in members:
            self.name_to_id_dict[member['name']] = {
                'user_id': member['employee_id'],
                'open_id': member['open_id'],
                'union_id': member['union_id'],
            }

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
                break
        return ret

    def __get_user_id_with_name(self, username) -> str:
        """
        :param username: 用户名 
        根据用户名获取user_id，找不到时返回None
        """
        if username in self.name_to_id_dict.keys():
            return self.name_to_id_dict[username]['user_id']
        else:
            self.__update_department_members()
            if username in self.name_to_id_dict.keys():
                return self.name_to_id_dict[username]['user_id']
            else:
                print('[RobotArsenal.__get_user_id_with_name] 机器人所在部门找不到用户名为\'{0}\'的成员'.format(username))
                return None

    def __get_open_id_with_name(self, username) -> str:
        """
        :param username: 用户名 
        根据用户名获取open_id，找不到时返回None
        """
        if username in self.name_to_id_dict.keys():
            return self.name_to_id_dict[username]['open_id']
        else:
            self.__update_department_members()
            print('[RobotArsenal.__get_open_id_with_name] 机器人所在部门找不到用户名为\'{0}\'的成员'.format(username))
            return None

    def __get_members_in_chat(self, chat_id: str) -> list:
        """
        获取群组中的关键用户信息列表 [{'open_id':,'user_id':}...]
        """
        print("[RobotArsenal.__get_members_in_chat] chat_id:{0}".format(chat_id))
        url = "https://open.feishu.cn/open-apis/chat/v4/info?chat_id={0}".format(chat_id)
        data = self.__request(url, None, None, 'GET')
        members = data.get("members")
        return members

    def __process_at_message(self, at_content) -> str:
        """
        处理艾特信息，将艾特内容转化为open_id或者所有人
        不存在的艾特信息将被替换为空字符串
        """
        at_content = at_content[1] # 用户名所在位置
        if at_content == at_all_pattern:
            return at_format_output.format(at_all_replace)

        open_id =  self.__get_open_id_with_name(at_content)
        if open_id == None:
            return ""
        else:
            return at_format_output.format(open_id)
        
    def __preprocess_message(self, message:str) -> str:
        """
        对文本信息进行预处理，返回处理后的信息
        1. 将@信息转换为富文本
        """
        message = message + ' '
        result = re.sub(at_pattern, self.__process_at_message, message)
        return result

    def __preprocess_rich_message(self, raw_message:str) -> list:
        """
        实验性功能
        将文本信息转化为富文本列表
        """
        # 预处理的预处理
        message = re.sub(strip_pattern, '', raw_message)
        if len(message) != len(raw_message):
            print("[RobotArsenal.__preprocess_rich_message] 处理富文本时删减了部分文本，发送内容为:\n\033[1;33m{0}\033[0m".format(message))
        message_save = message

        cur_idx = 0
        pre_idx = -1
        line_size = 0
        content = []
        while len(message) != 0 and cur_idx < len(message_save):
            if pre_idx == cur_idx:
                print("[RobotArsenal.__preprocess_rich_message] 处理富文本时出错！请检查{0}是否符合要求".format(message))
                content.clear()
                break
            pre_idx = cur_idx

            # print(message.replace('\n', '\\n'))
            # print("idx: " + str(cur_idx))
            if line_size == len(content):
                content.append([])
            
            if message.startswith('\n'):
                cur_idx = cur_idx + 1
                line_size = line_size + 1
                message = message_save[cur_idx:]
                continue

            # 普通字符串
            matchObj = re.match(at_pattern, message)
            if matchObj:
                content[line_size].append({
                    "tag": "at",
                    "user_id": self.get_user_id_with_name(matchObj.group(1)),
                })
                match_locate = matchObj.span()[1]
                cur_idx = cur_idx + match_locate
                message = message_save[cur_idx:]
                continue

            # 超链接
            matchObj = re.match(url_pattern, message)
            if matchObj:
                content[line_size].append({
                    "tag": "a",
                    "text": matchObj.group().strip(),
                    "href": matchObj.group().strip(),
                })
                match_locate = matchObj.span()[1]
                cur_idx = cur_idx + match_locate
                message = message_save[cur_idx:]
                continue

            matchObj = re.match(common_text_pattern, message)
            if matchObj:
                content[line_size].append({
                    "tag": "text",
                    "un_escape": True,
                    "text": re.sub(r'\s', '&nbsp;', matchObj.group(0)),
                    # "text": matchObj.group(0),
                })
                match_locate = matchObj.span()[1]
                cur_idx = cur_idx + match_locate
                message = message_save[cur_idx:]
                continue

            if message_save[cur_idx] == ' ':
                cur_idx = cur_idx + 1
                message = message_save[cur_idx:]
                continue

        return content

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

    def send_rich_message_to_chat(self, open_chat_id: str=None, chat_name: str='', title: str='title', content: str='', international: str='zh_cn'):
        """
        将富文本消息发送到群聊，注意每种功能（@，超链接，普通字符串）后要加上空格
        :param open_chat_id: 群聊ID
        :param chat_name: 群聊名
        :param title: 富文本标题
        :param content: 富文本
        :param international: 地区
        """
        post_message = {
            international: {
                "title": title,
                "content": self.__preprocess_rich_message(content),
            }
        }
        chat_id = open_chat_id or self.__get_chat_id_with_name(chat_name)
        if chat_id != "":
            self.__send_rich_message(post_message, "chat_id", chat_id)
        else:
            print("[RobotArsenal.send_message_to_chat] 未找到群聊\"{0}\"".format(chat_name))

    def send_message_to_user(self, message: str, username: str):
        """
        将消息私聊发送给用户
        :param message: 需要发送的消息
        :param username: 用户名
        """
        user_id = self.__get_user_id_with_name(username)
        if user_id != "":
            self.__send_message(message, "user_id", user_id)
        else:
            print("[RobotArsenal.send_message_to_user] 未找到用户\"{0}\"".format(username))

    def send_rich_message_to_user(self, username: str, title: str='title', content: str='', international: str='zh_cn'):
        """
        将富文本消息发送给用户，注意每种功能（@，超链接，普通字符串）后要加上空格
        :param username: 用户名
        :param title: 富文本标题
        :param content: 富文本
        :param international: 地区
        """
        post_message = {
            international: {
                "title": title,
                "content": self.__preprocess_rich_message(content),
            }
        }
        user_id = self.__get_user_id_with_name(username)
        if user_id != "":
            self.__send_rich_message(post_message, "user_id", user_id)
        else:
            print("[RobotArsenal.send_rich_message_to_user] 未找到用户\"{0}\"".format(username))

    def send_message_to_user_with_userid(self, message, user_id):
        """
        发送私聊消息给user_id制定的用户
        :param message: 需要发送的消息
        :param user_id: 用户id
        """
        self.__send_message(message, "user_id", user_id)

    def get_members_in_chat(self, open_chat_id: str=None, chat_name: str=""):
        """
        获取群聊中用户信息列表 [{'open_id':,'user_id':}...]
        :param chat_name: 群聊名
        :param open_chat_id: 群聊openid
        """
        if open_chat_id is None:
            chat_id = self.__get_chat_id_with_name(chat_name)
        else:
            chat_id = open_chat_id
        
        if chat_id == "":
            print("[RobotArsenal.get_members_in_chat] 未找到群聊\"{0}\"".format(chat_name))
            return None
        
        members = self.__get_members_in_chat(chat_id)
        return members

    def get_user_id_with_name(self, username):
        """
        :param username: 用户名 
        根据用户名获取user_id，找不到时返回None
        """
        if username == at_all_pattern:
            return at_all_replace
        
        return self.__get_user_id_with_name(username)

    def get_chat_id_with_name(self, chat_name:str):
        return self.__get_chat_id_with_name(chat_name)

    def get_name_with_open_id(self, open_id:str):
        """
        :param open_id: 用户open_id
        根据open_id获取用户名，找不到时返回None
        """
        ret = None
        for username, user_id_info in self.name_to_id_dict.items():
            if user_id_info['open_id'] == open_id:
                ret = username
                break

        if ret == None:
            self.__update_department_members()

        return ret

    def update_department_members(self, ):
        self.__update_department_members()
    
