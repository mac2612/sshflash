#!/bin/bash

echo "Booting the Surgeon environment..."
sudo python util.py

echo "Waiting for Surgeon to come up..."
sleep 10

echo "Flashing the kernel..."
# Flash the kernel
ssh root@169.254.6.2  '/usr/sbin/flash_erase /dev/mtd1 0 0'
cat uImage | ssh root@169.254.6.2 '/usr/sbin/nandwrite -p /dev/mtd1 -'

echo "Flashing the root filesystem..."
# Flash the root filesystem.
ssh root@169.254.6.2 '/usr/sbin/ubiformat -y /dev/mtd2'
ssh root@169.254.6.2 '/usr/sbin/ubiattach -p /dev/mtd2'
sleep 1
ssh root@169.254.6.2 '/usr/sbin/ubimkvol /dev/ubi0 -N 2 -m'
sleep 1
# TODO: Fill in the size of rootfs.ubifs dynamically.
SIZE=`wc -c < rootfs.ubifs`
echo "Rootfs is $SIZE"
cat rootfs.ubifs | ssh root@169.254.6.2 '/usr/sbin/ubiupdatevol -s 75948032 /dev/ubi0_0 -'
sleep 1
ssh root@169.254.6.2 '/usr/sbin/ubidetach -d 0'

sleep 3
echo "Done! Rebooting the host."
ssh root@169.254.6.2 '/sbin/reboot'
