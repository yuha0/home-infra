# Ansible Server configuration

Ansible playbook for basic server setup and then bootstrap a [kubernetes-sigs/kubespray] cluster.

## Operations

Create a virtual environment and then install required package versions:

```
uv venv
uv pip install -r kubespray/requirements.txt
uv run ansible-playbook ...
```

See [official documentation site] for common operations like create/modify/delete clusters.

### Upgrade cluster

Kubespray community [recommends] copying the sample `group_vars` and then maintaining it separately. But how do you receve future updates the community made 

To upgrade the cluster from kubespray release v1 to v2:

```bash
# 1. In the submodule, checkout the next available version:
cd kubespray
git fetch --all
git checkout v2

# 2. Apply the upstream changes in `group_vars` to the copy, inspect carefully, fix all the conflicts
git diff --relative=inventory/sample v1 v2 -- inventory/sample/group_vars |
  GIT_ALTERNATE_OBJECT_DIRECTORIES=$(git rev-parse --absolute-git-dir)/objects git -C ../.. apply -3 --directory=ansible/inventory

# 3. Recreate the ansible python environment
cd ..
rm -rf .venv
uv venv
uv pip install -r kubespray/requirements.txt

# 4. Follow official docs instruction to upgrade the cluster:
uv run ansible-playbook cluster.yml -b -i inventory/k0.ini -e '{"upgrade_cluster_setup": true}'

```

[kubernetes-sigs/kubespray]: https://github.com/kubernetes-sigs/kubespray
[official documentation site]: https://kubespray.io
[recommends]: https://github.com/kubernetes-sigs/kubespray/blob/6107c6ab7cd48d1104b3e6a47308967c7dbcfa5d/docs/operations/integration.md?plain=1#L61
