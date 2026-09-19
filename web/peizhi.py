# -*- coding: utf-8 -*-
"""
peizhi.py —— 统一读取环境变量。

为什么单独抽一个文件：
    校验、客户端、Web 三层都要用到配置，如果到处 os.environ.get，
    换个变量名要改一堆地方，测试也没法注入假配置。集中在这里好改。

注意：API Key 只从环境变量读，永远不写死在代码里、不发给浏览器。
"""
import os


def qu_huanjing(ziduan_ming, moren_zhi=""):
    """读一个环境变量，顺手去掉首尾空格（复制粘贴很容易带空格）。"""
    zhi = os.environ.get(ziduan_ming, moren_zhi)
    return zhi.strip() if isinstance(zhi, str) else zhi


def qu_zhengshu(ziduan_ming, moren_zhi):
    """读整数环境变量，读不出来就用默认值，不让它把整个服务搞崩。"""
    yuan = qu_huanjing(ziduan_ming, str(moren_zhi))
    try:
        return int(yuan)
    except (TypeError, ValueError):
        return moren_zhi


class Peizhi:
    """运行期配置。字段名用拼音，方便和报告里的中文说明对上。"""

    def __init__(self):
        # Shlink 的基地址。容器里必须是 http://shlink:8080（服务名），
        # 写成 localhost 就会变成访问 Web 容器自己，这是本实验最常见的坑。
        self.shlink_jichu_url = qu_huanjing(
            "SHLINK_JICHU_URL", "http://127.0.0.1:8080"
        ).rstrip("/")

        # 管理密钥，只在服务端进程里存在
        self.shlink_api_key = qu_huanjing("SHLINK_API_KEY", "")

        # 长 URL 域名白名单，逗号分隔
        yuan_baimingdan = qu_huanjing(
            "CHANG_URL_BAIMINGDAN",
            "localhost,127.0.0.1,host.docker.internal,shlink",
        )
        self.chang_url_baimingdan = [
            x.strip().lower() for x in yuan_baimingdan.split(",") if x.strip()
        ]

        # 长 URL 长度上限。2048 是浏览器和多数代理的安全值。
        self.chang_url_zuidachangdu = qu_zhengshu("CHANG_URL_ZUIDACHANGDU", 2048)

        # 自主功能①：创建频率限制
        self.xianzhi_chuangjian_cishu = qu_zhengshu("XIANZHI_CHUANGJIAN_CISHU", 20)
        self.xianzhi_chuangjian_chuangkou_miao = qu_zhengshu(
            "XIANZHI_CHUANGJIAN_CHUANGKOU_MIAO", 60
        )

        # 自主功能②：有效期上限（天）
        self.xianzhi_zuidayouxiaoqi_tian = qu_zhengshu(
            "XIANZHI_ZUIDA_YOUXIAOQI_TIAN", 365
        )

        # 调用 Shlink 的超时（秒）。分成 connect / read 两个，方便定位问题。
        self.qingqiu_chaoshi = (3.05, 10)

    def api_key_yi_peizhi(self):
        """检查 Key 有没有配。没配就别去调 API 了，直接给用户一个清楚的提示。"""
        return bool(self.shlink_api_key)

    def baimingdan_mingxi(self):
        """给报告和界面看的一行文本。"""
        return ",".join(self.chang_url_baimingdan)
