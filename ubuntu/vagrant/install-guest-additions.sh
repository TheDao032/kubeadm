#!/bin/bash
GUEST_ADDITION_VERSION=7.0.20
GUEST_ADDITION_ISO=VBoxGuestAdditions_${GUEST_ADDITION_VERSION}.iso
GUEST_ADDITION_MOUNT=/media/VBoxGuestAdditions

sudo apt-get install linux-headers-$(uname -r) build-essential dkms bzip2 -y

sudo wget http://download.virtualbox.org/virtualbox/${GUEST_ADDITION_VERSION}/${GUEST_ADDITION_ISO}
sudo mkdir -p ${GUEST_ADDITION_MOUNT}
sudo mount -o loop,ro ${GUEST_ADDITION_ISO} ${GUEST_ADDITION_MOUNT}
sudo sh ${GUEST_ADDITION_MOUNT}/VBoxLinuxAdditions.run
sudo rm ${GUEST_ADDITION_ISO}
sudo umount ${GUEST_ADDITION_MOUNT}
sudo rmdir ${GUEST_ADDITION_MOUNT}
