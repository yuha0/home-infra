# Cilium Hubble UI Ingress

Yes, this is just an ingress object for the already existing Hubble UI pod. The actual Hubble components are managed by Kubespray ansible tasks.

## Why not GitOps

1. [Kubespray cannot deploy a cluster without a CNI](https://github.com/kubernetes-sigs/kubespray/issues/8458). So cilium have to be installed by Kubespray.
2. Hubble is tightly integrated with cilium. So, to enable Hubble, my options are:
    - Letting kubespray install both cilium and hubble
    - Enable but not install Hubble with Kubespray. Later install Hubble with ["standalone" method in the helm chart](https://github.com/cilium/cilium/blob/0ef7f73dc0e631d038181fcdfe6697a5b1803857/install/kubernetes/cilium/values.yaml#L889). And I will need to spend hours of my life dealing with discrepancies between Kubespray and Hubble chart (secret naming convention, certificate path...etc) and watching all future changes in the two projects.
    - Deploy cluster with a very basic cni, `cni`, and later replace it with cilium. And since Kubespray expects itself to be the owner of CNI, I would expect a lot of issues in future cluster modifications.
3. I like that Kubespray project is vetting CNI plugin versions for me. I don't want to manage CNI myself if I don't have to.
