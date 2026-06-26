"""
日期工具函数
"""
from datetime import date, datetime, timedelta
from typing import List, Tuple


def today() -> date:
    """返回今天日期"""
    return date.today()


def yesterday() -> date:
    """返回昨天日期"""
    return date.today() - timedelta(days=1)


def date_range(start: date, end: date) -> List[date]:
    """生成日期范围列表"""
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def date_range_str(start: date, end: date, fmt: str = "%m/%d") -> List[str]:
    """生成日期范围的格式化字符串列表"""
    return [d.strftime(fmt) for d in date_range(start, end)]


def parse_date(date_str: str) -> date:
    """解析日期字符串 YYYY-MM-DD"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def get_week_range(end_date: date = None) -> Tuple[date, date]:
    """获取最近7天的日期范围"""
    end = end_date or today()
    start = end - timedelta(days=6)
    return start, end


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    return d.strftime(fmt)


def is_today(d: date) -> bool:
    """判断是否今天"""
    return d == today()
