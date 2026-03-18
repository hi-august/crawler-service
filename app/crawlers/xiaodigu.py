"""
小嘀咕爬虫实现
"""
from app.core.http_client import httpx_get
from app.core.notifier import notify_wechat
import portalocker
from app.core.lock import acquire_file_lock
from app.core.state_manager import StateManager
from app.utils.logger import cron_log
from app.utils.text import should_skip_similarity, format_link

XDGLT_URL = 'https://app.xdglt.com/mag/info/v2/channel/infoListByCatId?cat_id=138&channel_id=59'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)',
    'content-type': 'application/x-www-form-urlencoded'
}

# 全局状态管理器实例（可在 main 中初始化后传入，此处简化）
state_mgr = StateManager()


def crawl():
    """执行小嘀咕爬虫"""
    lock_fd = acquire_file_lock()
    if not lock_fd:
        cron_log.info("未获得锁，跳过本次小嘀咕爬虫执行")
        return

    try:
        cron_log.info("开始执行小嘀咕爬虫...")
        response = httpx_get(XDGLT_URL, headers=HEADERS, timeout=15)
        items = response.json()['list']
        new_titles = []
        cron_log.info(f"当前 seen_titles 数量: {len(state_mgr.seen_titles)}")

        first_run = state_mgr.get_crawler_state('xiaodigu') == 0

        for item in items:
            sharedata = item.get('sharedata', {})
            if not sharedata:
                continue

            title = sharedata['title']
            url = sharedata['linkurl']

            if not state_mgr.is_new_title(title):
                continue

            if not first_run:
                if should_skip_similarity(title, state_mgr.seen_titles):
                    continue
                title = format_link(title)

            cron_log.info(f"发现新标题: {title}")
            msg = f'小嘀咕 {title} {url}'
            new_titles.append(title)
            notify_wechat(msg)

        if new_titles:
            state_mgr.add_titles(new_titles)

        state_mgr.set_crawler_state('xiaodigu', 1)
        cron_log.info(f"小嘀咕爬虫执行完成，新增 {len(new_titles)} 条")
    except Exception as e:
        cron_log.error(f"小嘀咕爬虫出错: {e}")
    finally:
        if lock_fd:
            portalocker.unlock(lock_fd)  # 显式释放锁（可选）
            lock_fd.close()
