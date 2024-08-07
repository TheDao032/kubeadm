#!/bin/bash
#
# Sets up the kernel with the requirements for running Kubernetes
set -e

# Add br_netfilter kernel module
cat <<EOF >> /etc/modules
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
br_netfilter
nf_conntrack
EOF
systemctl restart systemd-modules-load.service

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system
