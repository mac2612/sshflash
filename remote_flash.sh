#!/bin/bash

# We use a public/private keypair to authenticate. 
# Surgeon uses the 169.254.8.X subnet to differentiate itself from
# a fully booted system for safety purposes.
SSH="ssh -i keys/id_rsa root@169.254.8.1"

# Size of the rootfs to be flashed, in bytes.
ROOTFS_SIZE=`wc -c < rootfs.ubifs`

# Fix the permissions on the "private" key, so ssh doesn't complain.
chmod 700 keys/id_rsa

echo "Leapster flash utility - installs a custom OS on your leapster!"
echo
echo "WARNING! This utility will ERASE the stock leapster OS and any other"
echo "data on the device. The device can be restored to stock settings using"
echo "the LeapFrog Connect app. Note that flashing your device will likely"
echo "VOID YOUR WARRANTY! Proceed at your own risk."
echo
echo "Please power off your leapster, hold the L + R shoulder buttons (LeapsterGS), "
echo "or right arrow + home buttons (LeapPad2), and then press power."
echo "You should see a screen with a green background."

read -p "Press enter when you're ready to continue." 

echo "Booting the Surgeon environment..."
sudo python util.py

echo "Waiting for Surgeon to come up..."
sleep 10

echo "Flashing the kernel..."
# For the first ssh command, skip hostkey checking to avoid prompting the user.
${SSH} -o "StrictHostKeyChecking no" '/usr/sbin/flash_erase /dev/mtd1 0 0'
cat uImage | ${SSH} '/usr/sbin/nandwrite -p /dev/mtd1 -'

echo "Flashing the root filesystem..."
${SSH} '/usr/sbin/ubiformat -y /dev/mtd2'
${SSH} '/usr/sbin/ubiattach -p /dev/mtd2'
sleep 1
${SSH} '/usr/sbin/ubimkvol /dev/ubi0 -N 2 -m'
sleep 1
echo "Writing rootfs image ($ROOTFS_SIZE bytes)..."
cat rootfs.ubifs | ${SSH} "/usr/sbin/ubiupdatevol -s $ROOTFS_SIZE /dev/ubi0_0 -"
sleep 1
${SSH} '/usr/sbin/ubidetach -d 0'

sleep 3
echo "Done! Rebooting the host."
${SSH} '/sbin/reboot'
