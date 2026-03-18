"""
FastAPI 应用，定时执行小嘀咕爬虫
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.crawlers import xiaodigu
from app.core.state_manager import StateManager
from app.utils.logger import cron_log

# 全局状态管理器实例
state_mgr = StateManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载状态已在 StateManager 初始化时完成
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        xiaodigu.crawl,
        trigger=IntervalTrigger(seconds=27),
        id='xiaodigu_crawler',
        replace_existing=True
    )
    scheduler.start()
    cron_log.info("调度器已启动，每27秒执行一次小嘀咕爬虫")
    yield
    scheduler.shutdown()
    # 移除 state_mgr.save()，避免覆盖
    cron_log.info("应用关闭，调度器已停止")


app = FastAPI(
    lifespan=lifespan,
    title="小嘀咕爬虫服务",
    description="定时抓取小嘀咕新内容并通过微信通知，支持手动触发和状态查看。"
)


@app.get("/")
async def root():
    return {"message": "小嘀咕爬虫服务运行中，每27秒自动抓取新内容"}


@app.get("/run")
async def manual_run(background_tasks: BackgroundTasks):
    """手动触发一次爬虫"""
    background_tasks.add_task(xiaodigu.crawl)
    return {"status": "triggered", "message": "小嘀咕爬虫已加入后台任务"}


@app.get("/status")
async def get_status():
    """获取当前状态"""
    return {
        "titles_count": len(state_mgr.seen_titles),
        "states": state_mgr.crawler_states,
        "last_titles": state_mgr.seen_titles[-10:]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
