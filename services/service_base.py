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
        self.on_init()

    def on_init(self, ):
        """
        子类自定义初始化操作
        """

    def check_args(self, ) -> bool:
        """
        检查命令参数是否合法
        """

    def invalid_args_process(self, ):
        """
        非法参数处理
        """

    def process(self, raw_data:dict) -> bool:
        """
        处理命令
        """