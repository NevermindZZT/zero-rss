FROM python:3.11-slim

ARG APP_VERSION=dev

LABEL org.opencontainers.image.title="zero-rss-backend" \
	org.opencontainers.image.version="${APP_VERSION}"

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY src/ ./src/

# 创建数据目录和脚本目录
RUN mkdir -p /data /app/scripts

# 暴露端口
EXPOSE 11080

# 启动
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "11080"]
