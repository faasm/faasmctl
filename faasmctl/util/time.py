from datetime import datetime


def get_time_rfc3339():
    time_now = datetime.now()
    return time_now.strftime("%Y-%m-%dT%H:%M:%SZ")
