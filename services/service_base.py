from robot_arsenal import RobotArsenal
from enum import Enum
import time

class ServiceFailure(Enum):
    ERROR_WRONG_ARGS = 0,
    ERROR_NO_GROUP_FOUND = 1,
    ERROR_USERNAME_NOT_FOUND = 2,
    ERROR_UNKNOWN_USER_OR_GROUP = 3,
    ERROR_UNEXPECTED = 999,

class ServiceFailureMessage:
    message_dict = {
        ServiceFailure.ERROR_WRONG_ARGS : "命令参数错误！",
        ServiceFailure.ERROR_NO_GROUP_FOUND : "未能找到群组",
        ServiceFailure.ERROR_USERNAME_NOT_FOUND : "未能找到用户名",
        ServiceFailure.ERROR_UNKNOWN_USER_OR_GROUP : "未知服务发起人/发起群组",
        ServiceFailure.ERROR_UNEXPECTED : "未知错误",
    }


class ServiceBase:
    """
    机器人聊天服务基类
    """
    LABEL = "base"
    LOG_FORMAT_STR = "[Service][{0}] {1}"

    def __init__(self, bot: RobotArsenal, args:list=[]):
        self.bot = bot
        self.args = args
        # 服务发起人
        self.open_id = None
        # 服务发起对话
        self.open_chat_id = None
        self.on_init()

    def on_init(self, ):
        """
        子类自定义初始化操作
        """

    def check_args(self, raw_data:dict) -> bool:
        """
        检查命令参数是否合法
        """
        if raw_data == None:
            return False
        
        self.open_id = raw_data.get("open_id", "")
        self.open_chat_id = raw_data.get("open_chat_id", "")
        if self.open_id == "" or self.open_chat_id == "":
            self.invalid_args_process(ServiceFailure.ERROR_UNKNOWN_USER_OR_GROUP)
            return False
        
        return True

    def invalid_args_process(self, error_type: ServiceFailure, args: list=None) -> str:
        """
        非法参数处理，基类不做打印日志以外处理，返回错误信息
        """
        error_message = self.get_error_message(error_type)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log = self.LOG_FORMAT_STR.format(time_str, error_message)
        print(log)
        return error_message

    def process(self, raw_data:dict) -> bool:
        """
        处理命令
        """
        return self.check_args(raw_data)
    
    def get_error_message(self, error_type: ServiceFailure):
        message = ServiceFailureMessage.message_dict[ServiceFailure.ERROR_UNEXPECTED]
        if isinstance(error_type, ServiceFailure):
            if error_type in ServiceFailureMessage.message_dict.keys():
                message = ServiceFailureMessage.message_dict[error_type]
        return message