# -*- mode: ruby -*-
# vi:set ft=ruby sw=2 ts=2 sts=2:

# Set the build mode
# "BRIDGE" - Places VMs on your local network so cluster can be accessed from browser.
#            You must have enough spare IPs on your network for the cluster nodes.
# "NAT"    - Places VMs in a private virtual network. Cluster cannot be accessed
#            without setting up a port forwarding rule for every NodePort exposed.
#            Use this mode if for some reason BRIDGE doesn't work for you.
BUILD_MODE = "NAT"

# Define how much memory your computer has in GB (e.g. 8, 16)
# Larger nodes will be created if you have more.
RAM_SIZE = 16

# Define how mnay CPU cores you have.
# More powerful workers will be created if you have more
CPU_CORES = 8


# Define the number of worker nodes
# If this number is changed, remember to update setup-hosts.sh script with the new hosts IP details in /etc/hosts of each VM.
NUM_CONTROLLER_NODES = 2
NUM_WORKER_NODES = 2

# Network parameters for NAT mode
IP_NW = "192.168.56"
# Host address start points
MASTER_IP_START = 10
NODE_IP_START = 20
LB_IP_START = 30

# Calculate resource amounts
# based on RAM/CPU
ram_selector = (RAM_SIZE / 4) * 4
if ram_selector < 8
  raise "Unsufficient memory #{RAM_SIZE}GB. min 8GB"
end
RESOURCES = {
  "control" => {
    1 => {
      # controlplane01 bigger since it may run e2e tests.
      "ram" => [ram_selector * 128, 2048].max(),
      "cpu" => CPU_CORES >= 12 ? 4 : 2,
    },
    2 => {
      # All additional masters get this
      "ram" => [ram_selector * 128, 2048].min(),
      "cpu" => CPU_CORES > 8 ? 2 : 1,
    },
  },
  "worker" => {
    "ram" => [ram_selector * 128, 4096].min(),
    "cpu" => (((CPU_CORES / 4) * 4) - 4) / 4,
  },
}

# Host operating sysem detection
module OS
  def OS.windows?
    (/cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM) != nil
  end

  def OS.mac?
    (/darwin/ =~ RUBY_PLATFORM) != nil
  end

  def OS.unix?
    !OS.windows?
  end

  def OS.linux?
    OS.unix? and not OS.mac?
  end

  def OS.jruby?
    RUBY_ENGINE == "jruby"
  end
end

# Determine host adpater for bridging in BRIDGE mode
def get_bridge_adapter()
  if OS.windows?
    return %x{powershell -Command "Get-NetRoute -DestinationPrefix 0.0.0.0/0 | Get-NetAdapter | Select-Object -ExpandProperty InterfaceDescription"}.chomp
  elsif OS.linux?
    return %x{ip route | grep default | awk '{ print $5 }'}.chomp
  elsif OS.mac?
    return %x{mac/mac-bridge.sh}.chomp
  end
end

# Helper method to get the machine ID of a node.
# This will only be present if the node has been
# created in VirtualBox.
def get_machine_id(vm_name)
  machine_id_filepath = ".vagrant/machines/#{vm_name}/virtualbox/id"
  if not File.exist? machine_id_filepath
    return nil
  else
    return File.read(machine_id_filepath)
  end
end

# Helper method to determine whether all nodes are up
def all_nodes_up()
  if get_machine_id("loadbalancer").nil?
    return false
  end

  (1..NUM_CONTROLLER_NODES).each do |i|
    if get_machine_id("controlplane#{i}").nil?
      return false
    end
  end

  (1..NUM_WORKER_NODES).each do |i|
    if get_machine_id("node#{i}").nil?
      return false
    end
  end
  return true
end

# Sets up hosts file and DNS
def setup_dns(node)
  # Set up /etc/hosts
  node.vm.provision "setup-hosts", :type => "shell", :path => "ubuntu/vagrant/setup-hosts.sh" do |s|
    s.args = [IP_NW, BUILD_MODE, NUM_CONTROLLER_NODES, NUM_WORKER_NODES, MASTER_IP_START, NODE_IP_START, LB_IP_START]
  end
  # Set up DNS resolution
  node.vm.provision "setup-dns", type: "shell", :path => "ubuntu/update-dns.sh"
end

# Runs provisioning steps that are required by masters and workers
def provision_kubernetes_node(node)
  # Set up DNS
  setup_dns node
  # Set up kernel parameters, modules and tunables
  node.vm.provision "setup-kernel", :type => "shell", :path => "ubuntu/setup-kernel.sh"
  # Set up ssh
  node.vm.provision "setup-ssh", :type => "shell", :path => "ubuntu/ssh.sh"
  # Set up guest additions
  # node.vm.provision "setup-guest-additions", :type => "shell", :path => "ubuntu/vagrant/install-guest-additions.sh"
end

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  # config.vm.box = "base"

  config.vm.box = "ubuntu/jammy64"
  config.vm.boot_timeout = 900

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  config.vm.box_check_update = false
  config.vbguest.auto_update = true

  # Provision Master Nodes
  (1..NUM_CONTROLLER_NODES).each do |i|
    config.vm.define "controlplane#{i}" do |node|
      # Name shown in the GUI
      node.vm.provider "virtualbox" do |vb|
        vb.name = "controlplane#{i}"
        vb.memory = RESOURCES["control"][i > 2 ? 2 : i]["ram"]
        vb.cpus = RESOURCES["control"][i > 2 ? 2 : i]["cpu"]
        vb.customize ["storageattach", :id, "--storagectl", "IDE", "--port", 1, "--device", 0, "--type", "dvddrive", "--medium", "/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions_7.0.20.iso"]
      end

      # config.vm.provision "shell", inline: <<-SHELL
      #   if ! mount | grep -q "/mnt"; then
      #     sudo mkdir -p /mnt
      #     sudo mount /dev/cdrom /mnt
      #     sudo apt install bzip2 -y
      #     sudo sh /mnt/VBoxLinuxAdditions.run || true
      #   fi
      # SHELL

      node.vm.hostname = "controlplane#{i}"
      if BUILD_MODE == "BRIDGE"
        adapter = ""
        node.vm.network :public_network, bridge: get_bridge_adapter()
      else
        node.vm.network :private_network, ip: IP_NW + ".#{MASTER_IP_START + i}"
        node.vm.network "forwarded_port", guest: 22, host: "#{2710 + i}"
      end
      provision_kubernetes_node node
      # Install (opinionated) configs for vim and tmux on master-1. These used by the author for CKA exam.
      if i == 1
        node.vm.provision "file", source: "./ubuntu/tmux.conf", destination: "$HOME/.tmux.conf"
        node.vm.provision "file", source: "./ubuntu/vimrc", destination: "$HOME/.vimrc"
        node.vm.provision "file", source: "./tools/approve-csr.sh", destination: "$HOME/approve-csr.sh"
      end
    end
  end

  # Provision Load Balancer Node
  config.vm.define "loadbalancer" do |node|
    node.vm.provider "virtualbox" do |vb|
      vb.name = "loadbalancer"
      vb.memory = 512
      vb.cpus = 1
      vb.customize ["storageattach", :id, "--storagectl", "IDE", "--port", 1, "--device", 0, "--type", "dvddrive", "--medium", "/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions_7.0.20.iso"]
    end

    # config.vm.provision "shell", inline: <<-SHELL
    #   if ! mount | grep -q "/mnt"; then
    #     sudo mkdir -p /mnt
    #     sudo mount /dev/cdrom /mnt
    #     sudo apt install bzip2 -y
    #     sudo sh /mnt/VBoxLinuxAdditions.run || true
    #   fi
    # SHELL

    node.vm.hostname = "loadbalancer"
    node.vm.network :private_network, ip: IP_NW + ".#{LB_IP_START}"
    node.vm.network "forwarded_port", guest: 22, host: 2730

    provision_kubernetes_node node
  end

  # Provision Worker Nodes
  (1..NUM_WORKER_NODES).each do |i|
    config.vm.define "node#{i}" do |node|
      node.vm.provider "virtualbox" do |vb|
        vb.name = "node#{i}"
        vb.memory = RESOURCES["worker"]["ram"]
        vb.cpus = RESOURCES["worker"]["cpu"]
        vb.customize ["storageattach", :id, "--storagectl", "IDE", "--port", 1, "--device", 0, "--type", "dvddrive", "--medium", "/Applications/VirtualBox.app/Contents/MacOS/VBoxGuestAdditions_7.0.20.iso"]
      end

      # config.vm.provision "shell", inline: <<-SHELL
      #   if ! mount | grep -q "/mnt"; then
      #     sudo mkdir -p /mnt
      #     sudo mount /dev/cdrom /mnt
      #     sudo apt install bzip2 -y
      #     sudo sh /mnt/VBoxLinuxAdditions.run || true
      #   fi
      # SHELL

      node.vm.hostname = "node#{i}"
      if BUILD_MODE == "BRIDGE"
        node.vm.network :public_network, bridge: get_bridge_adapter()
      else
        node.vm.network :private_network, ip: IP_NW + ".#{NODE_IP_START + i}"
        node.vm.network "forwarded_port", guest: 22, host: "#{2720 + i}"
      end
      provision_kubernetes_node node
    end
  end

  if BUILD_MODE == "BRIDGE"
    # Trigger that fires after each VM starts.
    # Does nothing until all the VMs have started, at which point it
    # gathers the IP addresses assigned to the bridge interfaces by DHCP
    # and pushes a hosts file to each node with these IPs.
    config.trigger.after :up do |trigger|
      trigger.name = "Post provisioner"
      trigger.ignore = [:destroy, :halt]
      trigger.ruby do |env, machine|
        if all_nodes_up()
          puts "    Gathering IP addresses of nodes..."
          nodes = ["loadbalancer"]
          ips = []
          (1..NUM_CONTROLLER_NODES).each do |i|
            nodes.push("controlplane#{i}")
          end
          (1..NUM_WORKER_NODES).each do |i|
            nodes.push("node#{i}")
          end
          nodes.each do |n|
            ips.push(%x{vagrant ssh #{n} -c 'public-ip'}.chomp)
          end
          hosts = ""
          ips.each_with_index do |ip, i|
            hosts << ip << "  " << nodes[i] << "\n"
          end
          puts "    Setting /etc/hosts on nodes..."
          File.open("hosts.tmp", "w") { |file| file.write(hosts) }
          nodes.each do |node|
            system("vagrant upload hosts.tmp /tmp/hosts.tmp #{node}")
            system("vagrant ssh #{node} -c 'cat /tmp/hosts.tmp | sudo tee -a /etc/hosts'")
            system("vagrant upload ~/.ssh/id_rsa.pub /tmp/id_rsa.pub #{node}")
            system("vagrant ssh #{node} -c 'cat /tmp/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys'")
          end
          File.delete("hosts.tmp")
          puts <<~EOF

                 VM build complete!

                 Use either of the following to access any NodePort services you create from your browser
                 replacing "port_number" with the number of your NodePort.

               EOF
          (1..ips.length).each do |i|
            puts "  http://#{ips[i]}:port_number"
          end
          puts ""
        else
          puts "    Nothing to do here"
        end
      end
    end
  else
    config.trigger.after :up do |trigger|
      trigger.name = "Post provisioner"
      trigger.ignore = [:destroy, :halt]
      trigger.ruby do |env, machine|
        if all_nodes_up()
          puts "    Gathering IP addresses of nodes..."
          nodes = ["loadbalancer"]
          ips = []
          (1..NUM_CONTROLLER_NODES).each do |i|
            nodes.push("controlplane#{i}")
          end
          (1..NUM_WORKER_NODES).each do |i|
            nodes.push("node#{i}")
          end
          nodes.each do |node|
            # ips.push(%x{vagrant ssh #{node} -c 'public-ip'}.chomp)
            system("vagrant upload ~/.ssh/id_rsa.pub /tmp/id_rsa.pub #{node}")
            system("vagrant ssh #{node} -c 'cat /tmp/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys'")
          end
          puts <<~EOF

                 VM build complete!

                 Use either of the following to access any NodePort services you create from your browser
                 replacing "port_number" with the number of your NodePort.

               EOF
        else
          puts "    Nothing to do here"
        end
      end
    end
  end
end
