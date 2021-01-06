# 使用这个脚本直接利用机器人发送请求使用服务器API
from urllib import parse
from robot_arsenal import RobotArsenal

APP_ID = "cli_9f58afd2fa2b900c"
APP_SECRET = "84Pb4n70TjT77dsN9VbxJdgtQkrRkJEC"

if __name__ == '__main__':
    bot = RobotArsenal(APP_ID, APP_SECRET)

    # 获取用户列表
    members = bot.get_members_in_chat('12点、18点吃饭群（尽量讨论工作）')
    print(str(members))

    # 获取所有用户 -> 建新群把所有人拉进去 -> 进群事件里面带有用户名
    # or 获取部门id -> 获取部门所有用户(需要权限)

    # for idx in range(30):
    #     bot.send_message_to_user_with_id('不会吧' + '?'*idx, '74c1f9bc')
    # bot.send_message_to_user_with_id('morning', 'a86adbec')
    # 'a86adbec' 我自己 '74c1f9bc' cjq 'e111153g' xg

    # bot.send_message_to_chat('<at user_id="74c1f9bc"></at> 不准录入', '12点、18点吃饭群（尽量讨论工作）')
    # bot.send_message_to_user('hello', parse.quote('陈柏铭'))
