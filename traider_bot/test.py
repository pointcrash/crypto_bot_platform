from datetime import datetime, timedelta

# Ваше время в миллисекундах
milliseconds = 1684738540559

# Преобразование миллисекунд в секунды и микросекунды
seconds = milliseconds // 1000

# Создание объекта datetime из полученных значений
target_time = datetime.fromtimestamp(seconds)

# Получение текущего времени
current_time = datetime.now()
print(current_time)
print(target_time)

# Вычисление разницы между текущим временем и целевым временем
time_difference = current_time - target_time

# Вычисление разницы в минутах
time_difference_in_minutes = time_difference.total_seconds() / 60

# Вывод разницы в минутах
print("Разница в минутах:", time_difference_in_minutes)
