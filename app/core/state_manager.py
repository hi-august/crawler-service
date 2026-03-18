"""
状态管理器：负责爬虫标题去重和运行状态的持久化
"""
import os
import json
import time
from datetime import datetime
from app.utils.logger import cron_log

# 获取项目根目录（当前工作目录）
BASE_DIR = os.getcwd()
# 默认状态文件路径：项目根目录下的 data/crawler_state.json
STATE_FILE = os.environ.get('CRAWLER_STATE_FILE', os.path.join(BASE_DIR, 'data', 'crawler_state.json'))


class StateManager:
    """状态管理器单例类"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, state_file=STATE_FILE):
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.state_file = state_file
        # 确保存放状态文件的目录存在
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        self.seen_titles = []      # 已处理过的标题列表
        self.crawler_states = {}    # 各爬虫的执行状态标记
        self.load()
        self._initialized = True

    def load(self):
        """从文件加载状态，若文件超过1.5天则自动重置"""
        if not os.path.exists(self.state_file):
            cron_log.info(f"状态文件不存在，将创建新文件: {self.state_file}")
            return

        try:
            file_mtime = os.path.getmtime(self.state_file)
            file_age = time.time() - file_mtime
            max_age = 1.5 * 24 * 60 * 60  # 1.5天

            if file_age > max_age:
                cron_log.info(f"状态文件已过期 ({file_age/3600:.1f}小时)，自动删除")
                os.remove(self.state_file)
                return

            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.seen_titles = data.get('titles', [])
                self.crawler_states = data.get('states', {})
                cron_log.info(f"加载状态: {len(self.seen_titles)} 个标题, {len(self.crawler_states)} 个状态")
        except Exception as e:
            cron_log.error(f"处理状态文件失败: {e}")

    def save(self):
        """保存当前状态到文件，并防止空数据覆盖已有文件"""
        # 如果内存中没有任何标题且没有任何状态标记，跳过保存（避免清空文件）
        if not self.seen_titles and not self.crawler_states:
            cron_log.warning("状态为空，跳过保存，避免覆盖已有文件")
            return

        try:
            # 限制标题数量，避免文件过大（保留最近10000条）
            limited_titles = self.seen_titles[-10000:] if len(self.seen_titles) > 10000 else self.seen_titles
            data = {
                'titles': limited_titles,
                'states': self.crawler_states,
                'last_update': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            cron_log.info(f"状态已保存: {len(limited_titles)} 个标题")
        except Exception as e:
            cron_log.error(f"保存状态文件失败: {e}")

    def is_new_title(self, title: str) -> bool:
        """检查标题是否未处理过"""
        return title not in self.seen_titles

    def add_titles(self, titles: list):
        """添加新标题并保存"""
        if titles:
            self.seen_titles.extend(titles)
            self.save()

    def set_crawler_state(self, name: str, value):
        """设置爬虫运行标记并保存"""
        self.crawler_states[name] = value
        self.save()

    def get_crawler_state(self, name: str, default=0):
        """获取爬虫运行标记"""
        return self.crawler_states.get(name, default)


# 全局单例访问函数
_state_manager_instance = None

def get_state_manager() -> StateManager:
    """获取全局唯一的状态管理器实例"""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance
