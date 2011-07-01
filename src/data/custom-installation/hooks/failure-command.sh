#!/bin/sh
set -x

if [ -e /host/ylmfos-livecd  ]; then
    zip -r /host/ylmfos-livecd /installation-logs.zip /var/log
fi
if [ -e /isodevice/ylmfos-livecd  ]; then
    zip -r /isodevice/ylmfos-livecd /installation-logs.zip /var/log
fi

msg="The installation failed. Logs have been saved in: /ylmfos-livecd /installation-logs.zip.\n\nNote that in verbose mode, the logs may include the password.\n\nThe system will now reboot."
if [ -x /usr/bin/zenity ]; then
    zenity --error --text "$msg"
elif [ -x /usr/bin/kdialog ]; then
    kdialog --msgbox "$msg"
elif [ -x /usr/bin/Xdialog ]; then
    Xdialog --msgbox "$msg"
fi

reboot
