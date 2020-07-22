#!/bin/sh

if [ $(id -u) -ne 0 ]
    then echo "You need to run this script as root."
    exit
fi

INSTALL_DIR="/opt/marcel-the-bot"

echo "Updating Marcel the Bot..."

su -c "/usr/bin/python3 -m pip install --user --upgrade -r requirements.txt" marcel
su -c "/usr/bin/python3 -m pip install --user --upgrade -r plugins-requirements.txt" marcel
su -c "/usr/bin/python3 -m pip install --user --upgrade marcel-the-bot" marcel

echo "Updating plugins..."

cp -r plugins/ "$INSTALL_DIR"
chown -R marcel:marcel "$INSTALL_DIR/plugins"
chmod -R 744 "$INSTALL_DIR/plugins"

echo "Restarting service..."

systemctl restart marcel-the-bot.service

echo "Finished updating!"