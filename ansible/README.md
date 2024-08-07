---
- name: Copy Nginx configuration file from template
  ansible.builtin.template:
    src: config.toml.j2
    dest: /etc/containerd/config.toml
    owner: root
    group: root
    mode: '0644'
