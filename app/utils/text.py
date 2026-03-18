"""
文本处理工具：相似度判断、小程序链接格式化
"""
import re
from Levenshtein import ratio


def should_skip_similarity(title: str, seen_titles: list, threshold: float = 0.3) -> bool:
    """
    判断标题是否因与最近 seen_titles 中的标题相似而应跳过。
    同时过滤包含特定银行关键词的标题。
    """
    # 检查与最近50条标题的相似度
    for prev_title in seen_titles[:-50:-1]:
        if ratio(prev_title, title) > threshold:
            return True

    # 屏蔽特定关键词
    if '交行' in title or '交通银行' in title:
        return True

    return False


def format_link(title: str) -> str:
    """
    如果标题中包含小程序链接，在链接后添加空格，避免微信中无法点击。
    """
    pattern = r'#小程序://[^\s]+/[A-Za-z0-9]+'
    match = re.search(pattern, title)
    if match:
        link = match.group(0)
        title = title.replace(link, f'{link} ')
    return title
