import os
import time

import django

from single_bot.logic.global_variables import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()


# def on_starting(server):
#     time.sleep(10)
#     lock.acquire()
#     try:
#         for thread in global_list_threads.values():
#             thread.start()
#     finally:
#         lock.release()
#
#
# def on_exit(server):
#     lock.acquire()
#     try:
#         global_list_bot_id.clear()
#     finally:
#         lock.release()


def when_ready(server):
    time.sleep(10)
    lock.acquire()
    try:
        server.log.info(global_list_threads.values())
        if global_list_threads.values():
            for thread in global_list_threads.values():
                thread.start()
                server.log.info(thread)
    finally:
        lock.release()
    server.log.info("Gunicorn is ready to accept requests.")


def worker_exit(server, worker):
    lock.acquire()
    try:
        server.log.info(global_list_bot_id)
        if global_list_bot_id:
            global_list_bot_id.clear()
    finally:
        lock.release()
    server.log.info(f"Worker {worker.pid} has exited.")
