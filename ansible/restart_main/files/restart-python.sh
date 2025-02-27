#/bin/sh
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <repos destination>"
    exit 1
fi

# Assign repos destination into the variable
repo_dest=$1

# Read main Python process PID
main_process_pid=$(cat "$repo_dest/bot-python/traider_bot/gunicorn.pid")

# Run migrate script and kill the main Python process
echo "Start migration"
docker exec main-1 python manage.py migrate
echo "Killing main process pid $main_process_pid to restart"
docker exec main-1 kill -HUP $main_process_pid
