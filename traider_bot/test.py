import re
from datetime import datetime, timedelta

pattern = r'\d{2}:\d{2}:\d{2} \d{4}-\d{2}-\d{2}'
input_string = "18:46:18 2023-08-17"

match = re.search(pattern, input_string)
if match:
    matched_text = match.group()
    datetime_obj = datetime.strptime(matched_text, '%H:%M:%S %Y-%m-%d')
    new_datetime = datetime_obj - timedelta(hours=1)
    print(datetime_obj)
