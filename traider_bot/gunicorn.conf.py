import os
import django

from single_bot.logic.global_variables import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()


def on_starting(server):
    lock.acquire()
    try:
        for thread in global_list_threads.values():
            thread.start()
    finally:
        lock.release()


# def on_exit(server):
#     pass
#
#
# def when_ready(server):
#     pass
#
#
# def worker_exit(server, worker):
#     pass
