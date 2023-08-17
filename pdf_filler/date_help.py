from datetime import datetime, timedelta

def get_datename(key: str) -> str:
    date_time_parts = key.split(' - ')
    date_str = date_time_parts[0]
    date = datetime.strptime(date_str, '%a, %d.%m.%y %H:%M')

    return date.strftime('%A')

def get_year(key: str) -> int:
    date_time_parts = key.split(' - ')
    date_str = date_time_parts[0]
    date = datetime.strptime(date_str, '%a, %d.%m.%y %H:%M')

    return int(date.strftime('%Y'))


def get_calendar_week(key: str) -> list:
    date_time_parts = key.split('  ')
    date_time_parts2 = date_time_parts[1].split('-')

    date_begin = datetime.strptime(date_time_parts2[0], '%d.%m.%Y')
    try:
        date_end = datetime.strptime(date_time_parts2[1], '%d.%m.%Y')
    except IndexError:
        date_end = date_begin

    calendar_weeks = []
    current_date = date_begin

    while current_date <= date_end:
        calendar_weeks.append(int(current_date.strftime('%W')))
        current_date += timedelta(weeks=1)

    calendar_weeks.reverse()

    return calendar_weeks

def get_sunday_of_week(week: int, year: int) -> str:
    sunday = datetime.strptime(f"{year}-W{week}-7", "%G-W%V-%u")
    
    return sunday.strftime("%d.%m.%Y")

def get_programmers_date(key: str) -> int:
    date_time_parts = key.split('  ')
    date_time_parts2 = date_time_parts[1].split('-')

    date_begin = datetime.strptime(date_time_parts2[0], '%d.%m.%Y')

    return date_begin.strftime('%Y%m%d')
