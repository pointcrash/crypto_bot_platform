import threading

lock = threading.Lock()
for i in range(10):
    if i == 1:
        lock.acquire()
    elif i == 6:
        lock.release()

if lock.locked():
    lock.release()
