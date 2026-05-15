from datetime import datetime, timedelta

def get_monday_date(dt: datetime) -> str:
    """
    해당 날짜가 속한 주의 월요일 날짜를 YYYY-MM-DD 형식으로 반환합니다.
    (월요일=0, 일요일=6)
    """
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")

def is_last_saturday(dt: datetime) -> bool:
    """
    해당 날짜가 그 달의 마지막 토요일인지 확인합니다.
    7일 뒤의 날짜가 현재 달과 다르면 마지막 주 토요일로 판단합니다.
    """
    if dt.weekday() != 5: # 5: Saturday
        return False
    
    next_week = dt + timedelta(days=7)
    return next_week.month != dt.month

def get_month_str(dt: datetime) -> str:
    """
    해당 날짜의 월을 YYYY-MM 형식으로 반환합니다.
    """
    return dt.strftime("%Y-%m")
