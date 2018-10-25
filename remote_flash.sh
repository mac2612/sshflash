#!/bin/bash

echo "Booting the Surgeon environment..."
sudo python util.py

echo "Waiting for Surgeon to come up..."
sleep 10

echo "Flashing the kernel..."
ssh -i keys/id_rsa root@169.254.6.2  '/usr/sbin/flash_erase /dev/mtd1 0 0'
cat uImage | ssh -i keys/id_rsa root@169.254.6.2 '/usr/sbin/nandwrite -p /dev/mtd1 -'

echo "Flashing the root filesystem..."
ssh -i keys/id_rsa root@169.254.6.2 '/usr/sbin/ubiformat -y /dev/mtd2'
ssh -i keys/id_rsa root@169.254.6.2 '/usr/sbin/ubiattach -p /dev/mtd2'
sleep 1
ssh -i keys/id_rsa root@169.254.6.2 '/usr/sbin/ubimkvol /dev/ubi0 -N 2 -m'
sleep 1
SIZE=`wc -c < rootfs.ubifs`
echo "Writing rootfs image ($SIZE bytes)..."
cat rootfs.ubifs | ssh -i keys/id_rsa root@169.254.6.2 "/usr/sbin/ubiupdatevol -s $SIZE /dev/ubi0_0 -"
sleep 1
ssh -i keys/id_rsa root@169.254.6.2 '/usr/sbin/ubidetach -d 0'

sleep 3
echo "Done! Rebooting the host."
ssh -i keys/id_rsa root@169.254.6.2 '/sbin/reboot'
