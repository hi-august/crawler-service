"""
文件锁工具，跨平台支持
"""
import os
import time
import portalocker
from app.utils.logger import cron_log

# Windows 下 /tmp 可能不存在，动态调整锁文件路径
LOCK_FILE = os.environ.get('CRAWLER_LOCK_FILE', '/tmp/crawler_lock.lock')
if os.name == 'nt' and LOCK_FILE.startswith('/tmp'):
    LOCK_FILE = os.path.join(os.getcwd(), 'crawler_lock.lock')

def acquire_file_lock(retries: int = 3, delay: int = 1):
    """
    尝试获取文件锁，失败重试，返回文件对象或 None
    """
    for attempt in range(retries):
        try:
            lock_fd = open(LOCK_FILE, 'w')
            portalocker.lock(lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
            return lock_fd
        except (IOError, OSError, portalocker.LockException) as e:
            if attempt < retries - 1:
                cron_log.warning(f"获取锁失败（尝试 {attempt+1}/{retries}），{delay}秒后重试。错误: {e}")
                time.sleep(delay)
            else:
                cron_log.error(f"无法获取锁，已重试 {retries} 次，跳过本次执行。")
                return None
    return None
