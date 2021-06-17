from services.service_base import ServiceBase
import json

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

    def check_args(self) -> bool:
        # TODO 2
        return super().check_args()

    def process(self, raw_data: dict) -> bool:
        if raw_data == None:
            return False
        # TODO 1
        return super().process(raw_data)