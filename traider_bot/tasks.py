import logging

from django_q.tasks import schedule
import datetime


# logging.basicConfig(level=logging.DEBUG)
#
# try:
#     schedule(
#         name='margin-check-task',
#         func='main.tasks.account_margin_check',
#         schedule_type='I',
#         minutes=1,
#         next_run=datetime.datetime.now(),
#         repeats=-1
#     )
#     logging.debug("Задача успешно запланирована")
# except Exception as e:
#     logging.error(f"Ошибка при планировании задачи: {e}")

def say_hello():
    print('Hello')
