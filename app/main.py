"""
合并后的 FastAPI 应用：
- 定时执行小嘀咕爬虫（每27秒）
- 提供 CORS 代理服务，用于访问 Rust API
"""

import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.crawlers import xiaodigu
from app.core.state_manager import StateManager
from app.utils.logger import cron_log
from app.config import RUST_API_BASE_URL, CRAWLER_INTERVAL_SECONDS, SERVICE_PORT, SERVICE_HOST

# 全局状态管理器实例
state_mgr = StateManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，启动和停止定时调度器"""
    # 启动时加载状态已在 StateManager 初始化时完成
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        xiaodigu.crawl,
        trigger=IntervalTrigger(seconds=CRAWLER_INTERVAL_SECONDS),
        id='xiaodigu_crawler',
        replace_existing=True
    )
    scheduler.start()
    cron_log.info(f"调度器已启动，每{CRAWLER_INTERVAL_SECONDS}秒执行一次小嘀咕爬虫")
    yield
    scheduler.shutdown()
    cron_log.info("应用关闭，调度器已停止")


app = FastAPI(
    lifespan=lifespan,
    title="小嘀咕爬虫 + CORS代理服务",
    description="定时抓取小嘀咕新内容并通过微信通知，同时提供CORS代理解决前端跨域问题。"
)

# 挂载静态文件目录（用于直接访问静态资源）
app.mount("/static", StaticFiles(directory="."), name="static")

# ====================== 小嘀咕爬虫相关路由 ======================
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

# ====================== CORS 代理相关路由 ======================
@app.get("/api/{tail:path}")
async def proxy_api(request: Request, tail: str):
    """代理 API 请求到 Rust 服务"""
    try:
        # 构建完整的 API URL
        api_url = f"{RUST_API_BASE_URL}/api/{tail}"
        # 复制查询参数
        query_params = dict(request.query_params)

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=query_params)

            # 构建响应，添加 CORS 头
            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get('content-type', 'application/json'),
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }
            )
    except Exception as e:
        import json
        error_response = json.dumps({"code": 500, "message": f"Proxy error: {str(e)}"})
        return Response(
            content=error_response,
            status_code=500,
            media_type="application/json",
            headers={'Access-Control-Allow-Origin': '*'}
        )

@app.options("/api/{tail:path}")
async def options_api():
    """处理 API OPTIONS 预检请求"""
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )

@app.get("/{path:path}")
async def serve_static(path: str):
    """提供静态文件服务（用于 HTML、CSS、JS 等）"""
    if os.path.exists(path):
        return FileResponse(
            path=path,
            headers={'Access-Control-Allow-Origin': '*'}
        )
    else:
        return Response("File not found", status_code=404)

@app.options("/{path:path}")
async def options_static():
    """处理静态文件 OPTIONS 预检请求"""
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    )


if __name__ == "__main__":
    import uvicorn
    print(f"服务运行在 http://localhost:{SERVICE_PORT}")
    print(f"爬虫状态: http://localhost:{SERVICE_PORT}/status")
    print(f"手动触发爬虫: http://localhost:{SERVICE_PORT}/run")
    print(f"前端页面: http://localhost:{SERVICE_PORT}/fund_table_optimized.html")
    print(f"API 代理示例: http://localhost:{SERVICE_PORT}/api/today_rt?authorize_user=august&is_filtered=0")
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
