# -*- coding: utf-8 -*-
"""
shlink_kehuduan.py —— 调用 Shlink REST API v3 的客户端。

对着 Shlink 5.1.6 的 REST Schema 写的，用到的接口：
    GET    /rest/health                                  健康检查
    POST   /rest/v3/short-urls                           创建短链
    GET    /rest/v3/short-urls                           短链列表（分页）
    GET    /rest/v3/short-urls/{shortCode}               单条详情
    GET    /rest/v3/short-urls/{shortCode}/visits        访问记录

X-Api-Key 只在这个模块里出现，且只在服务端发出，浏览器拿不到。
"""
import requests

from peizhi import Peizhi, qu_huanjing


class ShlinkCuowu(Exception):
    """把 Shlink 的错误包装一下，让 Web 层能区分「参数问题」和「依赖挂了」。"""

    def __init__(self, zhuangtai_ma, xiaoxi, yuanshi_ti=None):
        super().__init__(xiaoxi)
        self.zhuangtai_ma = zhuangtai_ma
        self.xiaoxi = xiaoxi
        self.yuanshi_ti = yuanshi_ti


class ShlinkKehuduan:
    def __init__(self, peizhi=None):
        self.peizhi = peizhi or Peizhi()

    # ---------- 内部工具 ----------

    def _tou(self):
        """请求头。Key 为空时也照发，让 Shlink 返回 401，我们不自己编造。"""
        return {
            "X-Api-Key": self.peizhi.shlink_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _qingqiu(self, fangfa, lujing, **kwargs):
        """统一发请求 + 统一把错误转成 ShlinkCuowu。"""
        dizhi = self.peizhi.shlink_jichu_url + lujing
        try:
            xiangying = requests.request(
                fangfa,
                dizhi,
                headers=self._tou(),
                timeout=self.peizhi.qingqiu_chaoshi,
                **kwargs
            )
        except requests.exceptions.ConnectTimeout:
            raise ShlinkCuowu(502, "连不上 Shlink（连接超时），检查服务是否启动")
        except requests.exceptions.ReadTimeout:
            raise ShlinkCuowu(504, "Shlink 响应超时，稍后重试")
        except requests.exceptions.ConnectionError:
            raise ShlinkCuowu(502, "连不上 Shlink，服务可能没起来或地址配错了")
        except requests.exceptions.RequestException as e:
            raise ShlinkCuowu(502, "调用 Shlink 失败：%s" % e)

        if xiangying.status_code >= 400:
            raise ShlinkCuowu(
                xiangying.status_code,
                self._ti_qu_cuowu_wenben(xiangying),
                xiangying.text[:500],
            )
        return xiangying

    @staticmethod
    def _ti_qu_cuowu_wenben(xiangying):
        """Shlink 的错误体是 {type, title, detail}，把 detail 挑出来最有用。"""
        try:
            shuju = xiangying.json()
        except ValueError:
            return "Shlink 返回 HTTP %d" % xiangying.status_code
        if isinstance(shuju, dict):
            return shuju.get("detail") or shuju.get("title") or (
                "Shlink 返回 HTTP %d" % xiangying.status_code
            )
        return "Shlink 返回 HTTP %d" % xiangying.status_code

    # ---------- 对外接口 ----------

    def jiankang(self):
        """健康检查。返回 (是否健康, 说明)。不抛异常，界面要能显示红绿灯。"""
        dizhi = self.peizhi.shlink_jichu_url + "/rest/health"
        try:
            xiangying = requests.get(dizhi, timeout=(2, 5))
        except requests.exceptions.RequestException as e:
            return False, "Shlink 不可达：%s" % e
        if xiangying.status_code != 200:
            return False, "Shlink 健康检查返回 HTTP %d" % xiangying.status_code
        try:
            ti = xiangying.json()
        except ValueError:
            return True, "Shlink 返回 200（响应体不是 JSON）"
        return True, "Shlink 状态：%s" % ti.get("status", "unknown")

    def chuangjian_duanlian(self, chang_url, zidingyi_duanma="", youxiao_tianshu=0,
                            biaoqian=None):
        """
        创建短链。

        youxiao_tianshu > 0 时换算成 Shlink 要的 validUntil（ISO8601）。
        这里用 UTC 的 Z 结尾格式，Shlink 5.1.6 认这个。
        """
        shiti = {"longUrl": chang_url}

        if zidingyi_duanma:
            # Shlink 里自定义短码的字段名就是 customSlug
            shiti["customSlug"] = zidingyi_duanma

        if youxiao_tianshu and youxiao_tianshu > 0:
            import datetime
            daoqi = datetime.datetime.now(datetime.timezone.utc) + \
                datetime.timedelta(days=youxiao_tianshu)
            shiti["validUntil"] = daoqi.replace(microsecond=0).isoformat().replace(
                "+00:00", "Z"
            )

        if biaoqian:
            shiti["tags"] = list(biaoqian)

        xiangying = self._qingqiu("POST", "/rest/v3/short-urls", json=shiti)
        return xiangying.json()

    def liebiao_duanlian(self, ye=1, meiye=20, paixu="dateCreated:DESC"):
        """短链列表。Shlink 的分页在 shortUrls.pagination 里。"""
        canshu = {"page": ye, "itemsPerPage": meiye, "orderBy": paixu}
        xiangying = self._qingqiu("GET", "/rest/v3/short-urls", params=canshu)
        return xiangying.json()

    def dan_tiao(self, duanma):
        xiangying = self._qingqiu("GET", "/rest/v3/short-urls/%s" % duanma)
        return xiangying.json()

    def fangwen_tongji(self, duanma, ye=1, meiye=20):
        """
        某条短链的访问记录。
        提醒：Shlink 的访问统计是异步落库的，刚才跳转完立刻查可能还是 0，
        界面上要提示「稍等几秒刷新」，不要一看到 0 就判定坏掉。
        """
        canshu = {"page": ye, "itemsPerPage": meiye}
        xiangying = self._qingqiu(
            "GET", "/rest/v3/short-urls/%s/visits" % duanma, params=canshu
        )
        return xiangying.json()

    def shan_chu(self, duanma):
        """删除短链（自主功能的界面上用得到）。"""
        self._qingqiu("DELETE", "/rest/v3/short-urls/%s" % duanma)
        return True

    def qu_suoyou(self, zuiduo=100):
        """
        把短链全捞出来（给统计用）。
        简单分页循环，最多捞 zuiduo 条，避免界面卡死。
        """
        jieguo = []
        ye = 1
        while len(jieguo) < zuiduo:
            ti = self.liebiao_duanlian(ye=ye, meiye=20)
            qu_kuai = ti.get("shortUrls", {})
            shuju = qu_kuai.get("data", []) or []
            jieguo.extend(shuju)
            fenye = qu_kuai.get("pagination", {}) or {}
            if ye >= (fenye.get("totalPages") or 1):
                break
            ye += 1
        return jieguo[:zuiduo]
