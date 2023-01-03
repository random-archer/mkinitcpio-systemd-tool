#!/usr/bin/busybox sh

# This file is part of https://github.com/random-archer/mkinitcpio-systemd-tool

source /etc/remotekey

for i in $(seq 1 ${REMOTE_KEY_TIMEOUT})
do
    if ping -c 1 -W 1 ${REMOTE_KEY_IP} &> /dev/null
    then
        dbclient -y ${REMOTE_KEY_USER}@${REMOTE_KEY_IP} "cat ${REMOTE_KEY_FILE}" > /root/${REMOTE_KEY_FILE}
        chmod 600 /root/${REMOTE_KEY_FILE}
        exit 0
    else
        sleep 1
    fi
done

echo "Failed to get ${REMOTE_KEY_FILE}"
