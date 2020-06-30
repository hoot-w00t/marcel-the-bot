#!/bin/sh

if [ $(id -u) -ne 0 ]
    then echo "You need to run this script as root."
    exit
fi

INSTALL_DIR="/opt/marcel-the-bot"

echo "Installing Marcel the Bot..."

adduser --system --shell /bin/bash --group --disabled-password marcel

su -c "/usr/bin/python3 -m pip install --user --upgrade -r requirements.txt" marcel
su -c "/usr/bin/python3 -m pip install --user --upgrade marcel-the-bot" marcel

mkdir -p "$INSTALL_DIR"
cp -ri plugins/ "$INSTALL_DIR"
chown -R marcel:marcel "$INSTALL_DIR"
chmod -R 744 "$INSTALL_DIR/plugins"
su -c "/usr/bin/python3 -m marcel -i '$INSTALL_DIR/cfg'" marcel
chmod 600 "$INSTALL_DIR/cfg/config.json"

echo "Creating service..."

mkdir -p /usr/lib/systemd/system

cp -i templates/marcel-the-bot.service /usr/lib/systemd/system

systemctl daemon-reload
systemctl enable marcel-the-bot.service

echo "Finished installing!"