#!/bin/bash

# Postfix SMTP Relay Setup Script for Ubuntu 24.04 + Exchange Online
# Run with sudo

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup.sh)"
  exit 1
fi

echo "--- Updating package list ---"
apt-get update

echo "--- Installing Postfix and dependencies ---"
# Pre-seed configuration to avoid interactive prompts
debconf-set-selections <<< "postfix postfix/mailname string $(hostname -f)"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
apt-get install -y postfix libsasl2-modules mailutils

echo "--- Backing up existing configuration ---"
cp /etc/postfix/main.cf /etc/postfix/main.cf.bak.$(date +%F-%T)
if [ -f /etc/postfix/sasl_passwd ]; then
    cp /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.bak.$(date +%F-%T)
fi

echo "--- Copying new configuration ---"
# Ensure the config files exist in the current directory
if [ ! -f main.cf ] || [ ! -f sasl_passwd ] || [ ! -f sender_access ] || [ ! -f recipient_access ]; then
    echo "Error: main.cf, sasl_passwd, sender_access, or recipient_access not found in current directory."
    exit 1
fi

cp main.cf /etc/postfix/main.cf
cp sasl_passwd /etc/postfix/sasl_passwd
cp sender_access /etc/postfix/sender_access
cp recipient_access /etc/postfix/recipient_access

echo "--- Configuring permissions and hashing credentials ---"
chmod 600 /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd
# Resulting database also needs to be secure
chmod 600 /etc/postfix/sasl_passwd.db

echo "--- Building restriction hash maps ---"
postmap /etc/postfix/sender_access
postmap /etc/postfix/recipient_access

echo "--- Restarting Postfix ---"
systemctl restart postfix
systemctl enable postfix

echo "--- Setup Complete ---"
echo "IMPORTANT: Please edit /etc/postfix/sasl_passwd with your actual credentials and run 'sudo postmap /etc/postfix/sasl_passwd' followed by 'sudo systemctl restart postfix'."
echo ""
echo "To test, run:"
echo "echo 'Subject: Test Email' | sendmail -v recipient@example.com"
