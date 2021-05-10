#! /bin/bash
# restart_robot.sh
pid=$(ps -ef | grep echo_bot.py | grep -v grep |  awk '{print $2}')
path=/home/edwardchen/workshop/FeishuRobotArsenal/
datetime=`date '+%Y%m%d-%H%M%S'`
log_full_path=$path/logs/$datetime.log

echo "---------- RESTART ECHO BOT ----------" >> $log_full_path 2>&1
echo "[$0] DATETIME:" $(date +"%Y-%m-%d %H:%M:%S") >> $log_full_path 2>&1

if test -z "$pid"
then
 echo "[$0] no pid found, continue" >> $log_full_path 2>&1
else
 echo "[$0] pid found: $pid" >> $log_full_path 2>&1
 kill $pid
 echo "[$0] kill $pid successfully" >> $log_full_path 2>&1
fi

echo "[$0] start echo_bot.py now" >> $log_full_path 2>&1
cd $path
python3 ./echo_bot.py >> $log_full_path 2>&1
