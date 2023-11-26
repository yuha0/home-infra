# Ansible Server configuration

![kubespray](https://img.shields.io/badge/kubespray-v2.22.0-green.svg)
![kubernetes](https://img.shields.io/badge/kubernetes-v1.26.5-green.svg)

Ansible playbook for basic server setup and then bootstrap a [kubernetes-sigs/kubespray] cluster.

## Tested environment

### Hardware

- [Raspberry Pi 4 Model B]
- [Intel NUC Kit NUC8i5BEK]

### Operating System

- [x] Debian 11

## Operations

Create a Python environment and then `pip install -r kubespray/requirements.txt`.

See [official documentation site] for common operations like create/modify/delete clusters.

### Upgrade cluster

Kubespray community [recommends] copying the sample `group_vars` and then maintaining it separately. But how do you receve future updates the community made 

To upgrade the cluster from kubespray release v1 to v2:

```bash
# 1. In the submodule, checkout the next available version:
cd kubespray
git fetch --all
git checkout v2

# 2. Generate a patch file with all the upstream changes in `group_vars`.
cd inventory/sample
git diff --relative v1 v2 group_vars > /tmp/group_vars.diff

# 3. Apply the diff to the copy, inspect carefully, fix all the conflicts
cd ../../../inventory
patch -s -p1 < /tmp/group_vars.diff

# 4. Upgrade the ansible python environment
cd ..
pip install --upgrade -r kubespray/requirements.txt

# 5. Follow official docs instruction to upgrade the cluster
```

[kubernetes-sigs/kubespray]: https://github.com/kubernetes-sigs/kubespray
[Raspberry Pi 4 Model B]: https://www.raspberrypi.org/products/raspberry-pi-4-model-b/
[Intel NUC Kit NUC8i5BEK]: https://www.intel.com/content/www/us/en/products/sku/126147/intel-nuc-kit-nuc8i5bek/specifications.html
[official documentation site]: https://kubespray.io
[recommends]: https://github.com/kubernetes-sigs/kubespray/blob/0f73d87509c780e76ed0463560f4ee271a9d5e44/docs/integration.md?plain=1#L47
