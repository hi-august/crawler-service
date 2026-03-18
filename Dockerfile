# 使用官方 Python 3.11 精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量：防止字节码缓存，输出不缓冲
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖（Levenshtein 需要编译，安装 gcc 和 python3-dev）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建数据目录用于持久化状态文件
RUN mkdir -p /data

EXPOSE 12315

# 启动命令：使用 uvicorn 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "12315"]
