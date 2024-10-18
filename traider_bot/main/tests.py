from datetime import datetime, timedelta
import time


def generate_date_ranges(start_time=None):
    current_time = datetime.now()

    if start_time:
        start_time = convert_timestamp_to_datetime(int(start_time) + 1)
    if not start_time or current_time - start_time > timedelta(days=90):
        start_time = current_time - timedelta(days=90)

    date_ranges = []

    while start_time < current_time:
        end_time = start_time + timedelta(days=7)
        if end_time > current_time:
            end_time = current_time
        start_ms = int(time.mktime(start_time.timetuple()) * 1000)
        end_ms = int(time.mktime(end_time.timetuple()) * 1000)
        date_ranges.append((start_ms, end_ms))
        start_time = end_time

    return date_ranges


def convert_timestamp_to_datetime(timestamp_ms):
    timestamp_sec = int(timestamp_ms) / 1000
    return datetime.fromtimestamp(timestamp_sec)

