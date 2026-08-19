"""
配置文件 - 统一管理所有配置项
"""

# Rust API 服务地址
RUST_API_BASE_URL = "http://192.168.32.88:12316"

# 通知服务 URL
NOTIFY_SERVICE_URL = f"{RUST_API_BASE_URL}/notify?authorize_user=august"

# 爬虫配置
CRAWLER_INTERVAL_SECONDS = 27

# 服务端口
SERVICE_PORT = 12315
SERVICE_HOST = "0.0.0.0"
