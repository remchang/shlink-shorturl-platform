# -*- coding: utf-8 -*-
"""
xianzhi.py —— 自主功能：创建频率限制（简单滑动窗口）。

为什么放在服务端：
    前端禁用按钮挡不住直接 curl 脚本。真正的限流必须服务端做。

局限（要写进报告，不能吹）：
    ① 计数放在进程内存里，所以 Dockerfile 里固定 --workers 1；
       多 worker 会各算各的窗口，等于没限。
    ② 服务重启计数清零。
    ③ 只按客户端 IP 限，NAT 后面的多个用户会互相影响。
    生产环境应该放 Redis 或者交给网关做。
"""
import threading
import time
from collections import deque


class PinlvXianzhi:
    """按 key（这里用客户端 IP）做滑动窗口计数。线程安全。"""

    def __init__(self, zuidacishu, chuangkou_miao):
        self.zuidacishu = max(1, int(zuidacishu))
        self.chuangkou_miao = max(1, int(chuangkou_miao))
        self._jilu = {}          # key -> deque[时间戳]
        self._suo = threading.Lock()

    def _qingli(self, duilie, xianzai):
        """把滑出窗口的时间戳扔掉。"""
        jiexian = xianzai - self.chuangkou_miao
        while duilie and duilie[0] <= jiexian:
            duilie.popleft()

    def yunxu(self, key):
        """
        尝试占用一次配额。
        返回 (是否允许, 剩余次数, 还要等几秒)。
        """
        xianzai = time.time()
        with self._suo:
            duilie = self._jilu.get(key)
            if duilie is None:
                duilie = deque()
                self._jilu[key] = duilie

            self._qingli(duilie, xianzai)

            if len(duilie) >= self.zuidacishu:
                # 最快也要等最早那次记录滑出窗口
                dengdai = int(duilie[0] + self.chuangkou_miao - xianzai) + 1
                return False, 0, max(1, dengdai)

            duilie.append(xianzai)
            shengyu = self.zuidacishu - len(duilie)
            return True, shengyu, 0

    def zhongzhi(self, key):
        """测试用：清掉某个 key 的记录。"""
        with self._suo:
            self._jilu.pop(key, None)

    def qingkong(self):
        """测试用：全清。"""
        with self._suo:
            self._jilu.clear()
