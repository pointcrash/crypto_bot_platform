import logging

from django_q.tasks import schedule
import datetime


def print_hello():
    print("Привет")
    logging.info("Привет")


schedule(
    name='margin-check-task',
    func='main.tasks.account_margin_check',
    schedule_type='I',
    minutes=1,
    next_run=datetime.datetime.now(),
    repeats=-1
)
