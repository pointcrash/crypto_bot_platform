import time

import requests


def start_ws_manager():
    url = "http://ws-manager:8008/ws/manager/start"
    print(url)
    print(requests.get(url))
    print(url)


# def deactivating_bots():
#     from django.db import transaction
#     with transaction.atomic():
#         Bot.objects.all().update_fields(is_active=False)


if __name__ == '__main__':
    time.sleep(3)
    start_ws_manager()
