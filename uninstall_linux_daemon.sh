#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

INSTALL_DIR="/opt/marcel-the-bot"

echo "Deleting service..."

systemctl stop marcel-the-bot.service
systemctl disable marcel-the-bot.service

rm -f /usr/lib/systemd/system/marcel-the-bot.service

systemctl daemon-reload

echo "Uninstalling Marcel the Bot..."

rm -rf "$INSTALL_DIR"
deluser --system --remove-home marcel

echo "Finished uninstalling!"