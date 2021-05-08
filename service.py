import re
import random
from robot_arsenal import RobotArsenal

private_chat_type = "private"
group_chat_type = "group"

roll_service_title = "\"roll {0}\"结果如下"
roll_label = "roll"
roll_error_param = "错误：命令格式为\"roll [人数]\""

def message_center(bot: RobotArsenal, chat_type: str, open_id: str, open_chat_id: str, text: str):
    if chat_type == private_chat_type:
        # do nothing now
        pass
    elif chat_type == group_chat_type:
        if text.find(roll_label):
            substr = text[text.find(roll_label):]
            all_numbers = re.findall('\d+', substr)
            if len(all_numbers) == 0:
                result_size = -1
            else:
                result_size = (int)(all_numbers[0])
            roll_and_notify(bot, result_size, open_chat_id, open_id)
        else:
            print("[message_center] unknown service!")
            

def roll_and_notify(bot: RobotArsenal, result_size: int, open_chat_id: str, open_id: str):
    """
    在open_chat_id群组中随机选出result_size名用户，并进行@通知
    :param open_chat_id: 群聊ID
    :param result_size: 选取用户
    :param open_id: 发起roll点的用户
    """
    if result_size == -1:
        bot.send_rich_message_to_chat(open_chat_id, title=roll_service_title.format(result_size), content=roll_error_param)
        return

    members = bot.get_members_in_chat(open_chat_id)
    if members is None:
        print("[service.roll_and_notify] 未找到 open_chat_id:{0} 对应群聊".format(open_chat_id))
        return
    
    random.shuffle(members) # 洗牌
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
        user_name = bot.get_name_with_open_id(member_open_id)

        # 未能取到用户名，跳过
        if str(user_name) == "None":
            print("[service.roll_and_notify] 未能找到open_id:{0}对应的用户名", member_open_id)
            continue
        member_names.append(user_name)
        # print(user_name)
    
    send_message = "result: "
    for member_name in member_names:
        send_message = send_message + "@{0} ".format(member_name)
    
    bot.send_rich_message_to_chat(open_chat_id, title=roll_service_title.format(result_size), content=send_message)