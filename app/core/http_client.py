"""
HTTP 请求封装，支持同步 GET/POST 带重试。
去除代理、并发执行等无关代码。
"""
import time
from typing import Optional, Dict

import httpx

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'


def _sync_request(method: str, url: str, **kwargs) -> Optional[httpx.Response]:
    """执行同步请求，内部使用，无重试"""
    try:
        resp = httpx.request(method, url, **kwargs)
        print(url, resp, resp.status_code)  # 可替换为 logger
        return resp
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def _request_with_retry(
    request_func,
    url: str,
    method: str = 'GET',
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs
) -> Optional[httpx.Response]:
    """带重试的请求装饰器"""
    headers = kwargs.pop('headers', {}) or {}
    headers.setdefault('User-Agent', USER_AGENT)

    for attempt in range(1, retries + 1):
        resp = request_func(method, url, headers=headers, **kwargs)
        if resp is not None and resp.status_code in (200, 301):
            return resp
        if attempt < retries:
            sleep_time = delay * (backoff ** (attempt - 1))
            print(f"Retry {attempt}/{retries} after {sleep_time:.1f}s for {url}")
            time.sleep(sleep_time)
        else:
            print(f"All {retries} retries failed for {url}")
            return None
    return None


def httpx_get(url: str, headers: Dict = None, retries: int = 3, **kwargs) -> Optional[httpx.Response]:
    """同步 GET 请求，带重试"""
    return _request_with_retry(_sync_request, url, method='GET', retries=retries, headers=headers, **kwargs)


def httpx_post(url: str, data: Dict = None, headers: Dict = None, retries: int = 3, **kwargs) -> Optional[httpx.Response]:
    """同步 POST 请求，带重试"""
    return _request_with_retry(_sync_request, url, method='POST', retries=retries, data=data, headers=headers, **kwargs)
