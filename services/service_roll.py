from services.service_base import ServiceBase, ServiceFailure
import json
import re
import random

no_disturb_json = "no_disturb_users.json"

class ServiceRoll(ServiceBase):
    """
    机器人聊天服务:roll点
    """
    LABEL = "roll"
    MESSAGE_NOT_GROUP_FOUND = "未找到 open_chat_id:{0} 对应群聊"
    MESSAGE_ROLL_RESULT_TITLE = "由用户 <{0}> 发起的 <roll {1}> 结果如下"
    MESSAGE_ROLL_ERROR_RESULT_TITLE = "发生了错误"
    MESSAGE_ROLL_RESULT_BODY = "{0}\n(共{1}人)"

    MESSAGE_LIST_RESULT_TITLE = "免打扰查询结果如下"
    MESSAGE_LIST_DISTURB_EMPTY = "免打扰名单为空"

    def on_init(self):
        fp = open(no_disturb_json, 'r', encoding='utf-8')
        # 免打扰用户字典 {服务 -> {群组 -> [用户], }, }
        self.no_disturb_dict = json.load(fp)
        # 服务发起人发送内容
        self.text = ""

    def invalid_args_process(self, error_type: ServiceFailure, args: list=None):
        error_message = super().invalid_args_process(error_type, args)
        if error_message == self.get_error_message(ServiceFailure.ERROR_UNKNOWN_USER_OR_GROUP):
            return
        
        self.bot.send_rich_message_to_chat(self.open_chat_id, title=self.MESSAGE_ROLL_ERROR_RESULT_TITLE, content=error_message)
        return

    def check_args(self, raw_data:dict) -> bool:
        if not super().check_args(raw_data):
            return False
        
        self.text = raw_data.get("text", "")
        if self.text == "":
            print("[service_roll] text is empty")
            return False
        
        index = self.text.find(self.LABEL)
        if index == -1:
            print("[service_roll] label not found")
            # message center 应该在查到 LABEL 后再实例化服务，这里是容错
            return False

        service_args = self.text[index:].split(' ')
        # 参数长度问题
        if len(service_args) <= 1:
            self.invalid_args_process(ServiceFailure.ERROR_WRONG_ARGS)
            return False
        
        self.args = service_args[1:]
        return True

    def process(self, raw_data:dict) -> bool:
        result = False
        if not super().process(raw_data):
            return result
        # roll 人数 0不包含自己1包含自己
        if self.args[0].isnumeric():
            result = self.__process_roll__()
        elif self.args[0] == "list":
            result = self.__process_list__()
        else:
            self.invalid_args_process(ServiceFailure.ERROR_WRONG_ARGS)
        return result

    def __process_roll__(self,) -> bool:
        self.roll_result_size = (int)(self.args[0])
        print('[process roll] {0}'.format(self.roll_result_size))
        members = self.bot.get_members_in_chat(self.open_chat_id)
        if members is None:
            self.invalid_args_process(ServiceFailure.ERROR_NO_GROUP_FOUND)
            return False
        
        random.shuffle(members)
        member_names = []
        idx = 0
        
        while len(member_names) < self.roll_result_size:
            if idx >= len(members):
                break
            member_open_id = members[idx]["open_id"]
            idx = idx + 1

            # 
            no_skip_self = len(self.args) >= 2 and self.args[1].isnumeric() and int(self.args[1]) == 1
            # roll 到自己，跳过
            if not no_skip_self and member_open_id == self.open_id:
                continue
            
            # roll 到免打扰，跳过
            if self.LABEL in self.no_disturb_dict.keys() and self.open_chat_id in self.no_disturb_dict[self.LABEL].keys():
                if member_open_id in self.no_disturb_dict[self.LABEL][self.open_chat_id]:
                    continue

            user_name = self.bot.get_name_with_open_id(member_open_id)
            if str(user_name) == "None":
                self.invalid_args_process(ServiceFailure.ERROR_USERNAME_NOT_FOUND)
                continue
            member_names.append(user_name)
            print(user_name)

        at_members = ""
        for member_name in member_names:
            at_members = at_members + "@{0} ".format(member_name)

        service_request_user = self.bot.get_name_with_open_id(self.open_id)
        if str(service_request_user) == "None":
                self.invalid_args_process(ServiceFailure.ERROR_USERNAME_NOT_FOUND)
                return False
        
        send_message = self.MESSAGE_ROLL_RESULT_BODY.format(at_members, len(member_names))
        send_title = self.MESSAGE_ROLL_RESULT_TITLE.format(service_request_user, self.roll_result_size)
        self.bot.send_rich_message_to_chat(self.open_chat_id, title=send_title, content=send_message)
        return True

    def __process_list__(self, ) -> bool:
        message = self.MESSAGE_LIST_DISTURB_EMPTY
        no_disturb_names = []
        if self.LABEL in self.no_disturb_dict.keys() and self.open_chat_id in self.no_disturb_dict[self.LABEL].keys():
            for member_open_id in self.no_disturb_dict[self.LABEL][self.open_chat_id]:
                no_disturb_name = self.bot.get_name_with_open_id(member_open_id)
                if str(no_disturb_name) == "None":
                    no_disturb_name = "未知({0})".format(member_open_id)
                no_disturb_names.append(no_disturb_name)
            if len(no_disturb_names) > 0:
                message = ""
            for i in range(0, len(no_disturb_names)):
                message = message + "{0}. {1} \n".format(i+1, no_disturb_names[i])
        self.bot.send_rich_message_to_chat(self.open_chat_id, title=self.MESSAGE_LIST_RESULT_TITLE, content=message)
        return True
