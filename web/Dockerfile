# ============================================================
# Web 管理界面镜像
#   要点：用 slim 基础镜像、先拷依赖清单再装（吃缓存）、非 root 运行、
#         只拷运行需要的文件、CMD 明确。
# ============================================================

# 固定小版本，不用 3-slim 这种会漂的标签
FROM python:3.12.7-slim

# 不写 .pyc、stdout 不缓冲（不然 docker logs 看不到东西）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ① 先只拷依赖清单 —— 只改代码不改依赖时，这一层能复用缓存，重建很快
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ② 再拷源码
COPY app.py peizhi.py shlink_kehuduan.py url_yanzheng.py xianzhi.py ./
COPY templates ./templates
COPY static ./static

# ③ 建非 root 用户，容器被攻破时拿不到 root
RUN useradd --create-home --shell /usr/sbin/nologin appren \
    && chown -R appren:appren /app
USER appren

EXPOSE 8501

# 单 worker：频率限制用的是进程内内存，多 worker 会各算各的，这里保持1个
CMD ["gunicorn", "--bind", "0.0.0.0:8501", "--workers", "1", "--threads", "4", \
     "--access-logfile", "-", "--error-logfile", "-", "app:app"]
