from datetime import datetime


def datetime_to_isoformat(date_time):
    return date_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def isoformat_to_datetime(isoformat):
    return datetime.strptime(isoformat[:-1] + "000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
