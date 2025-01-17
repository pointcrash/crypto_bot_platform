import time
from datetime import datetime

current_unix_time = int(time.time())

# Количество секунд в одном дне
seconds_in_a_day = 86400

# Вычитание одного дня
time_minus_one_day = current_unix_time - seconds_in_a_day

print(time_minus_one_day)
print(current_unix_time)