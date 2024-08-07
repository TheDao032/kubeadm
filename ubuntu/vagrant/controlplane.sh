{
POD_CIDR=10.200.0.0/16
SERVICE_CIDR=10.100.0.0/24

kubeadm init --pod-network-cidr $POD_CIDR --service-cidr $SERVICE_CIDR --apiserver-advertise-address $PRIMARY_IP

kubectl --kubeconfig /etc/kubernetes/admin.conf \
    apply -f "https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s-1.11.yaml"

}
