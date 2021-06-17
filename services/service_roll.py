from services.service_base import ServiceBase
import json
import re

no_disturb_json = "no_disturb_users.json"

class ServiceRoll(ServiceBase):
    """
    机器人聊天服务:roll点
    """
    LABEL = "roll"
    def on_init(self):
        fp = open(no_disturb_json, 'r', encoding='utf-8')
        # 免打扰用户字典 {服务 -> {群组 -> [用户], }, }
        self.no_disturb_dict = json.load(fp)
        # 服务发起人发送内容
        self.text = ""

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
        if len(service_args) <= 1:
            print("[service_roll] args not available")
            self.invalid_args_process()
            return False
        
        self.args = service_args[1:]
        return True

    def process(self, ) -> bool:
        result = False
        if re.match('\d+', self.args[0]):
            result = self.__process_roll__()
        return True

    def __process_roll__(self,) -> bool:
        print('[process roll] {0}'.format(self.args[0]))
        members = self.bot.get_members_in_chat(self.open_chat_id)
        if members is None:
            # TODO log and error message
            return False
        
        # TODO shuffle
        return True