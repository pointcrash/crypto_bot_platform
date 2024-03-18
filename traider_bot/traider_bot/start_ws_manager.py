import time

import requests


def start_ws_manager():
    url = "http://localhost:8008/ws/manager/start"
    requests.get(url)


if __name__ == '__main__':
    time.sleep(10)
    start_ws_manager()
