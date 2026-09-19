/* ============================================================
   短网址管理台前端逻辑
   纯原生 JS，不引框架。
   两个原则：
     ① 所有来自接口的文本都用 textContent 或转义后插入，不直接拼 innerHTML
        （短链的原网址是用户输入的，拼 HTML 就是给自己挖 XSS 的坑）
     ② 前端校验只是"提前提示"，真正的拦截在服务端，别以为前端能挡住人
   ============================================================ */

var dangqianYe = 1;
var zongYeShu = 1;
var wuTiaoShuju = [];       // 当前页原始数据，给搜索用
var gongkaiPeizhi = {};

/* ---------------- 小工具 ---------------- */

function zhuanYi(wenben) {
  if (wenben === null || wenben === undefined) return '';
  return String(wenben)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function tishi(wenben) {
  var kuang = document.getElementById('tishilan');
  kuang.textContent = wenben;
  kuang.hidden = false;
  clearTimeout(kuang._jishiqi);
  kuang._jishiqi = setTimeout(function () { kuang.hidden = true; }, 2200);
}

function geshihuaShijian(iso) {
  if (!iso) return '—';
  var riqi = new Date(iso);
  if (isNaN(riqi.getTime())) return iso;
  var b = function (n) { return n < 10 ? '0' + n : '' + n; };
  return riqi.getFullYear() + '-' + b(riqi.getMonth() + 1) + '-' + b(riqi.getDate())
    + ' ' + b(riqi.getHours()) + ':' + b(riqi.getMinutes());
}

async function diaoJiekou(lujing, xuanxiang) {
  var xiangying = await fetch(lujing, xuanxiang || {});
  var shuju;
  try {
    shuju = await xiangying.json();
  } catch (e) {
    throw new Error('服务器返回的不是 JSON（HTTP ' + xiangying.status + '）');
  }
  if (!xiangying.ok || shuju.ok === false) {
    var cuo = new Error(shuju.xiaoxi || ('请求失败 HTTP ' + xiangying.status));
    cuo.zhuangtai = xiangying.status;
    throw cuo;
  }
  return shuju;
}

/* ---------------- 顶栏健康灯 ---------------- */

async function shuaxinJiankang() {
  var web = document.getElementById('deng-web');
  var api = document.getElementById('deng-shlink');
  try {
    var ti = await diaoJiekou('/api/jiankang');
    web.className = 'deng hao';
    web.textContent = 'Web 正常';
    if (ti.shlink === 'ok') {
      api.className = 'deng hao';
      api.textContent = 'Shlink 正常';
    } else {
      api.className = 'deng huai';
      api.textContent = 'Shlink 异常';
      api.title = ti.shlink_shuoming || '';
    }
  } catch (e) {
    web.className = 'deng huai';
    web.textContent = 'Web 异常';
  }
}

/* ---------------- 汇总 ---------------- */

async function shuaxinHuizong() {
  try {
    var ti = await diaoJiekou('/api/huizong');
    document.getElementById('s-zong').textContent = ti.zong_duanlian_shu;
    document.getElementById('s-fangwen').textContent = ti.zong_fangwen_shu;
    document.getElementById('s-youxiao').textContent = ti.youxiao_shu;
    document.getElementById('s-guoqi').textContent = ti.guoqi_shu;
    document.getElementById('s-pingjun').textContent = ti.pingjun_fangwen;
  } catch (e) {
    /* 汇总失败不弹错，免得和主流程的错误提示打架 */
  }
}

/* ---------------- 创建短链 ---------------- */

function xianshiCuowu(wenben) {
  var kuang = document.getElementById('cuowu-qu');
  if (!wenben) { kuang.hidden = true; return; }
  kuang.textContent = wenben;
  kuang.hidden = false;
}

async function tichuangjian(shijian) {
  shijian.preventDefault();
  var anniu = document.getElementById('anniu-chuangjian');
  var changUrl = document.getElementById('chang-url').value.trim();
  var duanma = document.getElementById('zidingyi-duanma').value.trim();
  var youxiaoqi = document.getElementById('youxiaoqi').value.trim();

  xianshiCuowu('');
  document.getElementById('jieguo-qu').hidden = true;

  // 前端先做一遍最便宜的检查，少发一次没意义的请求
  if (!changUrl) {
    xianshiCuowu('长网址不能为空');
    return;
  }
  if (!/^https?:\/\//i.test(changUrl)) {
    xianshiCuowu('长网址要带 http:// 或 https:// 开头');
    return;
  }

  anniu.disabled = true;
  anniu.textContent = '生成中…';

  try {
    var ti = await diaoJiekou('/api/duanlian', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chang_url: changUrl,
        zidingyi_duanma: duanma,
        youxiao_tianshu: youxiaoqi === '' ? 0 : parseInt(youxiaoqi, 10)
      })
    });

    var lianjie = document.getElementById('jieguo-duan-url');
    lianjie.textContent = ti.duan_url;
    lianjie.href = ti.duan_url;
    document.getElementById('jieguo-chang-url').textContent = ti.chang_url;

    var tu = document.getElementById('jieguo-erweima');
    tu.src = '/api/erweima/' + encodeURIComponent(ti.duanma);
    tu.hidden = false;

    document.getElementById('jieguo-qu').hidden = false;
    if (typeof ti.shengyu_cishu === 'number') {
      document.getElementById('shengyu-cishu').textContent =
        '本窗口还能创建 ' + ti.shengyu_cishu + ' 条';
    }
    tishi('已生成 ' + ti.duanma);

    document.getElementById('chang-url').value = '';
    document.getElementById('zidingyi-duanma').value = '';
    document.getElementById('youxiaoqi').value = '';

    dangqianYe = 1;
    await shuaxinLiebiao();
    await shuaxinHuizong();
  } catch (e) {
    xianshiCuowu(e.message);
  } finally {
    anniu.disabled = false;
    anniu.textContent = '生成短链';
  }
}

/* ---------------- 列表 ---------------- */

function caozuoAnniu(duanma) {
  var an = String(duanma).replace(/'/g, "\\'");
  return '<div class="caozuo">'
    + '<button class="xiao" onclick="fuzhi(\'' + an + '\')">复制</button>'
    + '<button class="xiao" onclick="kanTongji(\'' + an + '\')">统计</button>'
    + '<button class="xiao" onclick="xiazaiErweima(\'' + an + '\')">二维码</button>'
    + '<button class="xiao wei" onclick="shanChu(\'' + an + '\')">删除</button>'
    + '</div>';
}

function tianchongLiebiao(qingdan) {
  var tbody = document.getElementById('liebiao-ti');
  if (!qingdan.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="kong">还没有短链，上面生成一条试试</td></tr>';
    return;
  }
  var hang = [];
  for (var i = 0; i < qingdan.length; i++) {
    var t = qingdan[i];
    var cishuLei = t.fangwen_cishu > 0 ? 'cishu' : 'cishu ling';
    var daoqi = t.youxiaoqi_jieshu
      ? '<span class="' + (t.yi_guoqi ? 'guoqi' : 'youxiao') + '">'
        + geshihuaShijian(t.youxiaoqi_jieshu) + '</span>'
      : '<span class="youxiao">永久</span>';

    hang.push(
      '<tr>'
      + '<td><span class="duanma" onclick="kanTongji(\'' + zhuanYi(t.duanma) + '\')">'
      + zhuanYi(t.duanma) + '</span></td>'
      + '<td><span class="lianjie" title="' + zhuanYi(t.chang_url) + '">'
      + zhuanYi(t.chang_url) + '</span></td>'
      + '<td><span class="' + cishuLei + '">' + t.fangwen_cishu + '</span></td>'
      + '<td>' + geshihuaShijian(t.chuangjian_shijian) + '</td>'
      + '<td>' + daoqi + '</td>'
      + '<td>' + caozuoAnniu(t.duanma) + '</td>'
      + '</tr>'
    );
  }
  tbody.innerHTML = hang.join('');
}

async function shuaxinLiebiao() {
  var tbody = document.getElementById('liebiao-ti');
  var guolv = document.getElementById('sousuo').value.trim().toLowerCase();
  try {
    var ti = await diaoJiekou('/api/duanlian?ye=' + dangqianYe + '&meiye=20');
    wuTiaoShuju = ti.qingdan;
    zongYeShu = ti.fenye.zong_ye_shu || 1;
    document.getElementById('ye-ma').textContent = dangqianYe + ' / ' + zongYeShu;

    var xianshi = wuTiaoShuju;
    if (guolv) {
      xianshi = wuTiaoShuju.filter(function (t) {
        return (t.duanma || '').toLowerCase().indexOf(guolv) >= 0
          || (t.chang_url || '').toLowerCase().indexOf(guolv) >= 0;
      });
    }
    tianchongLiebiao(xianshi);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" class="kong">加载失败：'
      + zhuanYi(e.message) + '</td></tr>';
  }
}

/* ---------------- 单条操作 ---------------- */

function fuzhi(duanma) {
  var dizhi = '';
  for (var i = 0; i < wuTiaoShuju.length; i++) {
    if (wuTiaoShuju[i].duanma === duanma) { dizhi = wuTiaoShuju[i].duan_url; break; }
  }
  if (!dizhi) { tishi('找不到这条短链'); return; }

  // navigator.clipboard 在 http 非 localhost 下不可用，得有个退路
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(dizhi).then(
      function () { tishi('已复制：' + dizhi); },
      function () { tishi(dizhi); }
    );
  } else {
    var shuru = document.createElement('textarea');
    shuru.value = dizhi;
    document.body.appendChild(shuru);
    shuru.select();
    try { document.execCommand('copy'); tishi('已复制：' + dizhi); }
    catch (e) { tishi(dizhi); }
    document.body.removeChild(shuru);
  }
}

function xiazaiErweima(duanma) {
  window.open('/api/erweima/' + encodeURIComponent(duanma) + '?xiazai=1', '_blank');
}

async function shanChu(duanma) {
  if (!confirm('确定删除短码 ' + duanma + ' 吗？删除后访问记录也会一起没。')) return;
  try {
    await diaoJiekou('/api/duanlian/' + encodeURIComponent(duanma), { method: 'DELETE' });
    tishi('已删除 ' + duanma);
    await shuaxinLiebiao();
    await shuaxinHuizong();
  } catch (e) {
    tishi('删除失败：' + e.message);
  }
}

/* ---------------- 统计抽屉 ---------------- */

function huachangtiao(biao) {
  var xiang = Object.keys(biao);
  if (!xiang.length) return '<p class="tishi">这个时间段没有记录</p>';
  var zuida = 1;
  for (var i = 0; i < xiang.length; i++) {
    if (biao[xiang[i]] > zuida) zuida = biao[xiang[i]];
  }
  var html = '';
  for (var j = 0; j < xiang.length; j++) {
    var ming = xiang[j];
    var shu = biao[ming];
    var kuan = Math.round(shu / zuida * 100);
    html += '<div class="tj-tiao">'
      + '<span class="ming" title="' + zhuanYi(ming) + '">' + zhuanYi(ming) + '</span>'
      + '<span class="tiao"><i style="width:' + kuan + '%"></i></span>'
      + '<span class="shu">' + shu + '</span>'
      + '</div>';
  }
  return html;
}

async function kanTongji(duanma) {
  var neirong = document.getElementById('chouti-neirong');
  document.getElementById('chouti-biaoti').textContent = '短码 ' + duanma + ' 的访问统计';
  neirong.innerHTML = '<p class="tishi">读取中…</p>';
  document.getElementById('zhezhao').hidden = false;

  try {
    var ti = await diaoJiekou('/api/duanlian/' + encodeURIComponent(duanma) + '/tongji');
    var html = '';
    html += '<div class="tj-kuai">';
    html += '<h4>累计访问</h4><div class="tj-da">' + ti.zong_fangwen + '</div>';
    html += '<p class="tishi">指向：' + zhuanYi(ti.chang_url) + '</p>';
    html += '<p class="tishi">到期：'
      + (ti.youxiaoqi_jieshu ? geshihuaShijian(ti.youxiaoqi_jieshu) : '永久') + '</p>';
    html += '</div>';
    html += '<div class="tj-kuai"><h4>按来源</h4>' + huachangtiao(ti.an_laiyuan) + '</div>';
    html += '<div class="tj-kuai"><h4>按日期</h4>' + huachangtiao(ti.an_tian) + '</div>';

    // 原始记录：这里故意用 textContent 逐条写，不拼 HTML
    html += '<div class="tj-kuai"><h4>最近访问记录（最多 20 条）</h4>';
    if (ti.zuijin_fangwen.length) {
      html += '<table class="liebiao"><thead><tr><th>时间</th><th>来源</th><th>UA</th></tr></thead><tbody>';
      for (var i = 0; i < ti.zuijin_fangwen.length; i++) {
        var ci = ti.zuijin_fangwen[i];
        html += '<tr><td>' + geshihuaShijian(ci.date) + '</td>'
          + '<td class="danhang" style="max-width:160px">' + zhuanYi(ci.referer || '直接访问') + '</td>'
          + '<td class="danhang" style="max-width:240px" title="' + zhuanYi(ci.userAgent || '') + '">'
          + zhuanYi((ci.userAgent || '').slice(0, 40)) + '</td></tr>';
      }
      html += '</tbody></table>';
    } else {
      html += '<p class="tishi">还没有访问记录</p>';
    }
    html += '</div>';

    if (ti.tishi) html += '<p class="tj-tishi">' + zhuanYi(ti.tishi) + '</p>';
    neirong.innerHTML = html;
  } catch (e) {
    neirong.innerHTML = '<div class="cuowu">' + zhuanYi(e.message) + '</div>';
  }
}

/* ---------------- 初始化 ---------------- */

async function jiazaiPeizhi() {
  try {
    gongkaiPeizhi = await diaoJiekou('/api/peizhi');
    document.getElementById('tishi-chang-url').textContent =
      '只允许：' + gongkaiPeizhi.chang_url_baimingdan.join(' / ');
    document.getElementById('youxiaoqi').max = gongkaiPeizhi.zuidayouxiaoqi_tian;
  } catch (e) { /* 拿不到就用页面上的静态提示 */ }
}

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('chuangjian-biaodan').addEventListener('submit', tichuangjian);
  document.getElementById('anniu-shuaxin').addEventListener('click', function () {
    shuaxinLiebiao(); shuaxinHuizong(); shuaxinJiankang();
  });
  document.getElementById('sousuo').addEventListener('input', shuaxinLiebiao);
  document.getElementById('shang-ye').addEventListener('click', function () {
    if (dangqianYe > 1) { dangqianYe--; shuaxinLiebiao(); }
  });
  document.getElementById('xia-ye').addEventListener('click', function () {
    if (dangqianYe < zongYeShu) { dangqianYe++; shuaxinLiebiao(); }
  });
  document.getElementById('guan-chouti').addEventListener('click', function () {
    document.getElementById('zhezhao').hidden = true;
  });
  document.getElementById('zhezhao').addEventListener('click', function (e) {
    if (e.target.id === 'zhezhao') document.getElementById('zhezhao').hidden = true;
  });

  jiazaiPeizhi();
  shuaxinJiankang();
  shuaxinLiebiao();
  shuaxinHuizong();
  setInterval(shuaxinJiankang, 30000);
});
