# Ansible k0s

Ansible playbook for basic server setup and then bootstrap a [k0s] cluster.

Many tasks are based on [movd/k0s-ansible], which is inspired by [kubernetes-sigs/kubespray] and [k3s-io/k3s-ansible], . Unlike those playbooks, this one does not aim to be generic or compatible for different use cases, but built to suit my own paticular environment, which is an Intel NUC mini PC and a bunch of Raspberry Pis.

[k0s]: https://github.com/k0sproject/k0s
[movd/k0s-ansible]: https://github.com/movd/k0s-ansible
[kubernetes-sigs/kubespray]: https://github.com/kubernetes-sigs/kubespray
[k3s-io/k3s-ansible]: https://github.com/k3s-io/k3s-ansible
