import re
import random
import json
from robot_arsenal import RobotArsenal

private_chat_type = "private"
group_chat_type = "group"

roll_service_title = "\"roll {0}\"结果如下"
roll_label = "roll"
roll_service_message = "抽选: {0}\n在review结束后请在发起人消息下点赞"
roll_error_param = "错误：命令格式为\"roll [人数]\""
roll_chat_no_found = "错误：无法获取对应群组成员，可能是凭证已过期"

no_disturb_json = "no_disturb_users.json"

class Service:
    def __init__(self, bot: RobotArsenal):
        """
        飞书机器人响应服务
        """
        self.bot = bot
        self.__init_no_disturb_dict()

    def __init_no_disturb_dict(self):
        fp = open(no_disturb_json, 'r', encoding='utf-8')
        # 免打扰用户字典 {服务 -> {群组 -> [用户], }, }
        self.no_disturb_dict = json.load(fp)

    def message_broadcast(self, chat_type: str, open_id: str, open_chat_id: str, text: str):
        if chat_type == private_chat_type:
            # do nothing now
            pass
        elif chat_type == group_chat_type:
            if text.find(roll_label) != -1:
                substr = text[text.find(roll_label):]
                all_numbers = re.findall('\d+', substr)
                if len(all_numbers) == 0:
                    result_size = -1
                else:
                    result_size = (int)(all_numbers[0])
                self.roll_and_notify(result_size, open_chat_id, open_id)
            else:
                print("[message_center] unknown service!")

    def roll_and_notify(self, result_size: int, open_chat_id: str, open_id: str):
        """
        在open_chat_id群组中随机选出result_size名用户，并进行@通知
        :param open_chat_id: 群聊ID
        :param result_size: 选取用户
        :param open_id: 发起roll点的用户
        """
        if result_size == -1:
            self.bot.send_rich_message_to_chat(open_chat_id, title=roll_service_title.format(
                result_size), content=roll_error_param)
            return

        members = self.bot.get_members_in_chat(open_chat_id)
        if members is None:
            error_message = "[service.roll_and_notify] 未找到 open_chat_id:{0} 对应群聊".format(open_chat_id)
            print(error_message)
            self.bot.send_rich_message_to_chat(open_chat_id, title=roll_service_title.format(
                result_size), content=roll_chat_no_found)
            return

        random.shuffle(members)  # 洗牌
        member_names = []
        idx = 0

        while len(member_names) < result_size:
            if idx >= len(members):
                break
            member_open_id = members[idx]["open_id"]
            idx = idx + 1
            # roll 到自己，跳过
            if member_open_id == open_id:
                continue

            # roll 到免打扰，跳过
            if roll_label in self.no_disturb_dict.keys() and open_chat_id in self.no_disturb_dict[roll_label].keys():
                if member_open_id in self.no_disturb_dict[roll_label][open_chat_id]:
                    continue

            user_name = self.bot.get_name_with_open_id(member_open_id)

            # 未能取到用户名，跳过
            if str(user_name) == "None":
                print(
                    "[service.roll_and_notify] 未能找到open_id:{0}对应的用户名", member_open_id)
                continue
            member_names.append(user_name)
            # print(user_name)

        at_members = ""
        for member_name in member_names:
            at_members = at_members + "@{0} ".format(member_name)

        send_message = roll_service_message.format(at_members)
        self.bot.send_rich_message_to_chat(open_chat_id, title=roll_service_title.format(
            result_size), content=send_message)
