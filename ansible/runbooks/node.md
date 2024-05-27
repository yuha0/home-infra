# Add a new node or rebuild an existing node

## Common

Whether it's a control plane or worker node, the first after getting a new server is to make it ready for running ansible against:

- Write down the root password, create one if the new server does not have that.
- Create a new user for SSH. This user will also have the ability to run passwordless sudo for all the future ansible opeartions after running `common.yml`.
- Install Python:
    - `apt-get update && apt-get install python3-dev -y`

Then you add the hostname to inventory file, run `common.yml`(enter the new user's password for SSH, and root password for switching to root):

```bash
ansible-playbook -kKi inventory/k0.ini -l <new-node> common.yml
```

This may not work if the new node does not have `sudo`. In that case, add argument `--become-method su` to the command.

## Add a worker node

This is as simple as running `cluster.yml`.

## Recover failed control plane node

Similar to the official runbook [recover-control-plane.md](https://github.com/kubernetes-sigs/kubespray/blob/5616a4a3eedf3462d25346f02afe57bf36ae77c3/docs/operations/recover-control-plane.md), except that instead of _copying_ the broken nodes to `broken_etcd`/`broken_kube_control_plane`, we should follow [the old version](https://github.com/kubernetes-sigs/kubespray/commit/a00b0c48fe00ef1b27a5245c8442f410679b9120) and _move_ them. That is, when `rpi2` went down, I rebuilt the same board and called it rpi9, even when it's the same hardware.

Even in bare metal environment, a node's life ends when it is wiped, and when I rebuild it again, it shall carry a new identity. Treating it as a brand new node makes operations easy, especially when kubespray is not fully idempotent.
