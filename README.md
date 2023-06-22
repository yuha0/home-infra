# Home Infrastructure

Here's the infrastructure-as-code repository for my home infrastructure.

The whole infrastructure is running in a Kubernetes cluster, which is managed by [kubernetes-sigs/kubespray](https://github.com/kubernetes-sigs/kubespray) based Ansible playbooks [here](ansible/).

Everything else is running in the Kubernetes cluster and managed with [GitOps](https://www.weave.works/technologies/gitops/) concept leveraging [ArgoCD](https://argo-cd.readthedocs.io).
