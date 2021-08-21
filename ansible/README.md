# Ansible k0s

Ansible playbook for basic server setup and then bootstrap a [k0s] cluster.

Many tasks are based on [movd/k0s-ansible], which is inspired by [kubernetes-sigs/kubespray] and [k3s-io/k3s-ansible]. Unlike those playbooks, this one does not aim to be generic or compatible for different use cases. _You may not like some of the opinionated design choices._

This playbook is idempotent, and is safe to be setup on an Ansible Tower/AWX instance to be executed repeatedly.

## Tested environment

### Hardware

- [Raspberry Pi 4 Model B]
- [Intel NUC Kit NUC8i5BEK]

### Operating System

- Debian 11

[k0s]: https://github.com/k0sproject/k0s
[movd/k0s-ansible]: https://github.com/movd/k0s-ansible
[kubernetes-sigs/kubespray]: https://github.com/kubernetes-sigs/kubespray
[k3s-io/k3s-ansible]: https://github.com/k3s-io/k3s-ansible
[Raspberry Pi 4 Model B]: https://www.raspberrypi.org/products/raspberry-pi-4-model-b/
[Intel NUC Kit NUC8i5BEK]: https://www.intel.com/content/www/us/en/products/sku/126147/intel-nuc-kit-nuc8i5bek/specifications.html
[v1.21.3+k0s.0]: https://github.com/k0sproject/k0s/releases/tag/v1.21.3%2Bk0s.0

