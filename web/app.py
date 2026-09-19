# -*- coding: utf-8 -*-
"""
app.py —— 自建 Web 管理界面（Flask）。

架构边界（很重要，报告里也要写）：
    浏览器  ──>  本服务(web)  ──X-Api-Key──>  Shlink API  ──>  PostgreSQL
                 ^^^^^^^                      ^^^^^^^
                 只有这里持有 Key              短链跳转不经过本服务

    也就是说：
      * 浏览器永远看不到 X-Api-Key，所有管理操作都由服务端代发；
      * 短链访问（GET /abc123）是 Shlink 自己处理的，本服务不参与转发，
        这样统计才准、也少一层单点。

本文件用工厂函数 chuangjian_app() 而不是模块级 app：
    测试的时候可以塞一个假的 Shlink 客户端进去，不用真的起容器。
"""
import io
import json

from flask import Flask, jsonify, render_template, request, send_file

from peizhi import Peizhi
from shlink_kehuduan import ShlinkCuowu, ShlinkKehuduan
from url_yanzheng import jianyan_chang_url, jianyan_duanma, jianyan_youxiaoqi
from xianzhi import PinlvXianzhi


def _cuowu(zhuangtai, xiaoxi, **qita):
    """统一的错误响应格式，前端只需要看 ok / xiaoxi 两个字段。"""
    ti = {"ok": False, "xiaoxi": xiaoxi}
    ti.update(qita)
    return jsonify(ti), zhuangtai


def chuangjian_app(peizhi_duixiang=None, kehuduan=None):
    pz = peizhi_duixiang or Peizhi()
    khd = kehuduan or ShlinkKehuduan(pz)

    # 频率限制器（自主功能①）
    xianzhi_qi = PinlvXianzhi(
        pz.xianzhi_chuangjian_cishu, pz.xianzhi_chuangjian_chuangkou_miao
    )

    app = Flask(__name__)
    # 让中文在 JSON 里直接显示，方便 curl 看结果
    app.json.ensure_ascii = False
    app.config["PEIZHI"] = pz
    app.config["XIANZHI_QI"] = xianzhi_qi

    # ---------------- 页面 ----------------

    @app.get("/")
    def shouye():
        return render_template("index.html")

    # ---------------- 健康检查 ----------------

    @app.get("/api/jiankang")
    def jiankang():
        """
        自己的健康检查。注意区分：
          · 本服务活着 != Shlink 活着。要分开报，不然排障时看不出是谁的问题。
        """
        shlink_hao, shlink_shuoming = khd.jiankang()
        return jsonify({
            "ok": True,
            "web": "ok",
            "shlink": "ok" if shlink_hao else "bad",
            "shlink_shuoming": shlink_shuoming,
            "api_key_yi_peizhi": pz.api_key_yi_peizhi(),
        })

    @app.get("/api/peizhi")
    def gongkai_peizhi():
        """
        发给前端的配置。★ 只发不敏感的东西：
        白名单、各项上限，方便界面做前置提示。API Key 绝对不在这里。
        """
        return jsonify({
            "ok": True,
            "chang_url_baimingdan": pz.chang_url_baimingdan,
            "zuidachangdu": pz.chang_url_zuidachangdu,
            "mei_chuangkou_cishu": pz.xianzhi_chuangjian_cishu,
            "chuangkou_miao": pz.xianzhi_chuangjian_chuangkou_miao,
            "zuidayouxiaoqi_tian": pz.xianzhi_zuidayouxiaoqi_tian,
        })

    # ---------------- 短链创建 ----------------

    @app.post("/api/duanlian")
    def chuangjian():
        # ➊ 取参数：前端可能用 JSON，也可能用表单，两种都容忍一下
        shuju = request.get_json(silent=True) or request.form or {}
        chang_url = shuju.get("chang_url", "")
        zidingyi_duanma = shuju.get("zidingyi_duanma", "") or ""
        youxiao_tianshu = shuju.get("youxiao_tianshu", 0)

        # ➋ 频率限制：放在最前面，非法请求也计数，
        #    不然攻击者可以用一堆非法请求白嫖（反正不计数）
        kehu_ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
        yunxu, shengyu, dengdai = xianzhi_qi.yunxu(kehu_ip)
        if not yunxu:
            return _cuowu(
                429,
                "创建太频繁了，请 %d 秒后再试" % dengdai,
                dengdai_miao=dengdai,
            )

        # ➌ 自己的校验层
        tongguo, cuowu_wen = jianyan_chang_url(
            chang_url, pz.chang_url_baimingdan, pz.chang_url_zuidachangdu
        )
        if not tongguo:
            return _cuowu(400, cuowu_wen, ziduan="chang_url")

        tongguo, cuowu_wen = jianyan_duanma(zidingyi_duanma)
        if not tongguo:
            return _cuowu(400, cuowu_wen, ziduan="zidingyi_duanma")

        tongguo, tianshu, cuowu_wen = jianyan_youxiaoqi(
            youxiao_tianshu, pz.xianzhi_zuidayouxiaoqi_tian
        )
        if not tongguo:
            return _cuowu(400, cuowu_wen, ziduan="youxiao_tianshu")

        # ➍ 代浏览器去调 Shlink
        try:
            jieguo = khd.chuangjian_duanlian(
                chang_url.strip(),
                zidingyi_duanma=zidingyi_duanma.strip(),
                youxiao_tianshu=tianshu,
            )
        except ShlinkCuowu as e:
            # Shlink 对「短码已存在」返回 400 + INVALID_SHORT_URL / 自定义短码冲突，
            # 这里翻译成用户能看懂的话，而不是把英文原文糊上去
            if e.zhuangtai_ma == 400 and zidingyi_duanma:
                return _cuowu(409, "短码 %s 已经被占用了，换一个吧" % zidingyi_duanma,
                              ziduan="zidingyi_duanma")
            if e.zhuangtai_ma == 401:
                return _cuowu(500, "服务端 API Key 无效，请检查 .env 里的 INITIAL_API_KEY")
            return _cuowu(502, "创建失败：%s" % e.xiaoxi)

        return jsonify({
            "ok": True,
            "duan_url": jieguo.get("shortUrl"),
            "duanma": jieguo.get("shortCode"),
            "chang_url": jieguo.get("longUrl"),
            "chuangjian_shijian": jieguo.get("dateCreated"),
            "youxiaoqi_tianshu": tianshu,
            "shengyu_cishu": shengyu,
        })

    # ---------------- 列表与统计 ----------------

    @app.get("/api/duanlian")
    def liebiao():
        ye = request.args.get("ye", 1, type=int)
        meiye = min(request.args.get("meiye", 20, type=int), 100)
        try:
            ti = khd.liebiao_duanlian(ye=ye, meiye=meiye)
        except ShlinkCuowu as e:
            return _cuowu(502, "读取列表失败：%s" % e.xiaoxi)

        qu_kuai = ti.get("shortUrls", {}) or {}
        shuju = qu_kuai.get("data", []) or []
        fenye = qu_kuai.get("pagination", {}) or {}

        # 整理成前端好用的扁平结构，顺便把 visitsSummary 里的总数提出来
        qingdan = []
        for tiao in shuju:
            zongji = (tiao.get("visitsSummary") or {}).get("total", 0)
            qingdan.append({
                "duanma": tiao.get("shortCode"),
                "duan_url": tiao.get("shortUrl"),
                "chang_url": tiao.get("longUrl"),
                "chuangjian_shijian": tiao.get("dateCreated"),
                "youxiaoqi_kaishi": tiao.get("validSince"),
                "youxiaoqi_jieshu": tiao.get("validUntil"),
                "fangwen_cishu": zongji,
                "biaoqian": tiao.get("tags", []) or [],
                "yi_guoqi": tiao.get("meta", {}).get("validUntil") is not None
                and tiao.get("meta", {}).get("isValid") is False,
            })

        return jsonify({
            "ok": True,
            "qingdan": qingdan,
            "fenye": {
                "dangqian_ye": fenye.get("currentPage", ye),
                "zong_ye_shu": fenye.get("totalPages", 1),
                "zong_tiao_shu": fenye.get("totalItems", len(qingdan)),
            },
        })

    @app.get("/api/duanlian/<duanma>/tongji")
    def tongji(duanma):
        try:
            xiangqing = khd.dan_tiao(duanma)
            fangwen = khd.fangwen_tongji(duanma, meiye=50)
        except ShlinkCuowu as e:
            if e.zhuangtai_ma == 404:
                return _cuowu(404, "没有找到短码 %s" % duanma)
            return _cuowu(502, "查询统计失败：%s" % e.xiaoxi)

        fangwen_shuju = (fangwen.get("visits") or {}).get("data", []) or []
        zongji = (xiangqing.get("visitsSummary") or {}).get("total", 0)

        # 按天/按来源粗略汇总，界面上画个小条形图
        an_tian = {}
        an_laiyuan = {}
        for ci in fangwen_shuju:
            ri = (ci.get("date") or "")[:10]
            if ri:
                an_tian[ri] = an_tian.get(ri, 0) + 1
            ly = ci.get("referer") or "直接访问"
            an_laiyuan[ly] = an_laiyuan.get(ly, 0) + 1

        return jsonify({
            "ok": True,
            "duanma": duanma,
            "duan_url": xiangqing.get("shortUrl"),
            "chang_url": xiangqing.get("longUrl"),
            "zong_fangwen": zongji,
            "youxiaoqi_jieshu": xiangqing.get("validUntil"),
            "zuijin_fangwen": fangwen_shuju[:20],
            "an_tian": an_tian,
            "an_laiyuan": dict(
                sorted(an_laiyuan.items(), key=lambda x: -x[1])[:8]
            ),
            "tishi": "Shlink 统计异步落库，刚访问完看数字没变是正常的，等几秒刷新",
        })

    @app.delete("/api/duanlian/<duanma>")
    def shan_chu(duanma):
        try:
            khd.shan_chu(duanma)
        except ShlinkCuowu as e:
            if e.zhuangtai_ma == 404:
                return _cuowu(404, "没有找到短码 %s" % duanma)
            return _cuowu(502, "删除失败：%s" % e.xiaoxi)
        return jsonify({"ok": True, "xiaoxi": "已删除 %s" % duanma})

    # ---------------- 自主功能②：二维码 ----------------

    @app.get("/api/erweima/<duanma>")
    def erweima(duanma):
        """
        给短链生成二维码。
        二维码内容是短链本身（不是长链），这样扫出来还能被统计到。
        """
        try:
            xiangqing = khd.dan_tiao(duanma)
        except ShlinkCuowu as e:
            if e.zhuangtai_ma == 404:
                return _cuowu(404, "没有找到短码 %s" % duanma)
            return _cuowu(502, "生成二维码失败：%s" % e.xiaoxi)

        duan_url = xiangqing.get("shortUrl") or ""
        if not duan_url:
            return _cuowu(500, "Shlink 没返回短链地址，没法生成二维码")

        try:
            import qrcode
        except ImportError:
            return _cuowu(500, "服务器没装 qrcode 库，请 pip install qrcode pillow")

        tupian = qrcode.make(duan_url)
        huancun = io.BytesIO()
        tupian.save(huancun, format="PNG")
        huancun.seek(0)
        return send_file(
            huancun,
            mimetype="image/png",
            as_attachment=request.args.get("xiazai") == "1",
            download_name="erweima-%s.png" % duanma,
        )

    # ---------------- 汇总（给 dashboard 卡片） ----------------

    @app.get("/api/huizong")
    def huizong():
        try:
            suo_you = khd.qu_suoyou(zuiduo=200)
        except ShlinkCuowu as e:
            return _cuowu(502, "汇总失败：%s" % e.xiaoxi)

        zong_shu = len(suo_you)
        zong_fangwen = 0
        youxiao_shu = 0
        for tiao in suo_you:
            zong_fangwen += (tiao.get("visitsSummary") or {}).get("total", 0)
            meta = tiao.get("meta") or {}
            if meta.get("isValid", True):
                youxiao_shu += 1

        return jsonify({
            "ok": True,
            "zong_duanlian_shu": zong_shu,
            "zong_fangwen_shu": zong_fangwen,
            "youxiao_shu": youxiao_shu,
            "guoqi_shu": zong_shu - youxiao_shu,
            "pingjun_fangwen": round(zong_fangwen / zong_shu, 2) if zong_shu else 0,
        })

    # ---------------- 统一异常兜底 ----------------

    @app.errorhandler(404)
    def mei_zhaodao(e):
        if request.path.startswith("/api/"):
            return _cuowu(404, "接口不存在：%s" % request.path)
        return render_template("index.html"), 200

    @app.errorhandler(500)
    def neibu_cuowu(e):
        # 不把堆栈甩给浏览器，只给一个 id 方便对日志
        return _cuowu(500, "服务器内部错误，看 docker logs duanlian-web")

    return app


# gunicorn 的入口
app = chuangjian_app()


if __name__ == "__main__":
    # 本地裸跑调试用：python app.py
    app.run(host="127.0.0.1", port=8501, debug=True)
