import datetime

a = 1714089600000 / 1000
b = 1714176000000 / 1000

print(datetime.datetime.fromtimestamp(a))
print(datetime.datetime.fromtimestamp(b))
print()

print(datetime.datetime.fromtimestamp(int(1713744000000 / 1000)))
print(datetime.datetime.fromtimestamp(int(1714176000000 / 1000)))
