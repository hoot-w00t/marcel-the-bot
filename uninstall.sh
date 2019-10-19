#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

echo "Deleting service..."

systemctl stop marcel-the-bot.service
systemctl disable marcel-the-bot.service

rm /usr/lib/systemd/system/marcel-the-bot.service

systemctl daemon-reload

echo "Uninstalling Marcel the Bot..."

rm -r /opt/marcel-the-bot/
rmdir -f /opt/marcel-the-bot/

deluser --system --remove-home marcel

echo "Finished uninstalling!"