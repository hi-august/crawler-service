# 第一阶段：构建阶段
FROM python:3.11-alpine AS builder

WORKDIR /app

# 安装编译依赖（gcc、musl-dev、python3-dev 等）
RUN apk add --no-cache \
    build-base \
    musl-dev \
    python3-dev \
    && rm -rf /var/cache/apk/*

# 设置环境变量：防止字节码缓存
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 复制依赖文件并安装 Python 包到虚拟环境
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.11-alpine

WORKDIR /app

# 安装运行时所需的系统库（如果有特殊依赖，例如 libpq、libffi 等，请在此添加）
# 此处只保留基础库，通常 alpine 基础镜像已满足，但如需可添加
# 例如：RUN apk add --no-cache libpq libffi

# 从 builder 阶段复制虚拟环境
COPY --from=builder /venv /venv

# 创建数据目录
RUN mkdir -p /data

# 设置环境变量，使用虚拟环境的 Python
ENV PATH="/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 12315

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "12315"]
