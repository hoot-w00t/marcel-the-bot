#!/bin/sh

if [ $(id -u) -ne 0 ]
  then echo "You need to run this script as root."
  exit
fi

echo "Installing Marcel the Bot..."

adduser --system --shell /bin/bash --group --disabled-password marcel

mkdir -p /opt/marcel-the-bot/

cp marcel.py /opt/marcel-the-bot/marcel.py
cp config.json /opt/marcel-the-bot/marcel.json
cp -r resources/ /opt/marcel-the-bot/resources/
cp -r plugins/ /opt/marcel-the-bot/plugins/

chown -R marcel:marcel /opt/marcel-the-bot/

chmod -R 744 /opt/marcel-the-bot/resources/
chmod -R 744 /opt/marcel-the-bot/plugins/
chmod 755 /opt/marcel-the-bot/marcel.py
chmod 600 /opt/marcel-the-bot/marcel.json

echo "Installing requirements.txt through PyPI..."

su -c "python3 -m pip install -U -r requirements.txt" marcel

echo "Creating service..."

mkdir -p /usr/lib/systemd/system/

cp marcel-the-bot.service /usr/lib/systemd/system/marcel-the-bot.service

systemctl daemon-reload
systemctl enable marcel-the-bot.service

echo "Finished installing!"