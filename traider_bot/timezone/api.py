# import requests
# import json
#
# import os
# import django
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
# django.setup()
#
# from timezone.models import TimeZone
#
#
# def set_timezones():
#     api_key = 'TENDMJ874ZEH'
#     url = f'http://api.timezonedb.com/v2.1/list-time-zone?key={api_key}'
#     response = json.loads(requests.get(url + '&format=json').text)
#
#     for zone in response['zones']:
#         TimeZone.objects.create(
#             countryCode=zone['countryCode'],
#             countryName=zone['countryName'],
#             zoneName=zone['zoneName'],
#             gmtOffset=zone['gmtOffset'],
#         )
