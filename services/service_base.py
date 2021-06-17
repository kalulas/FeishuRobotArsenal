from robot_arsenal import RobotArsenal

class ServiceBase:
    """
    机器人聊天服务基类
    """
    LABEL = "base"
    def __init__(self, bot: RobotArsenal, args:list=[]):
        self.bot = bot
        self.label = self.LABEL
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
            return False
        
        return True

    def invalid_args_process(self, ):
        """
        非法参数处理
        """

    def process(self, ) -> bool:
        """
        处理命令
        """
        