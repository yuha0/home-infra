# vigo

Controls a Samsung The Frame TV and exposes it to Apple Home. Source and the generic sample manifests: https://github.com/yuha0/vigo (`deploy/`). Changes from the sample:

- Real TV address, internal HTTPRoute, TrueNAS storage classes, CiliumNetworkPolicy for the database.
- The encryption keyring as a sealed secret (`sealed-vigo-keyring.yaml`). Keep a plain copy of `keyring.json` outside the cluster: the sealed secret only decrypts on this cluster, and a database backup is useless without the keyring.

## Manual steps

The namespace, PKI, database, network policy, keyring and `art` PVC were first applied by hand, then adopted by Argo CD under the same names. Don't rename `db` or `art`: Argo CD would create new ones, and the old data would be orphaned.

The `art` PV (TrueNAS SMB share) is declared in `core/volume.yaml` next to its claim, because `truenas-smb-general` sets neither of two things vigo needs: mount options `uid=65532,gid=65532,file_mode=0640,dir_mode=0750` (otherwise the share mounts as root with mode 0755 and non-root vigo-core can't write to it) and `persistentVolumeReclaimPolicy: Retain`. Mount option changes take effect on the next mount, so restart vigo-core after changing them. If the PVC is ever recreated, the new PV gets a new name: update `core/volume.yaml` to match.

## Network

- vigo-core: the TV only accepts WebSocket connections from its own subnet. The gateway masquerades lab traffic to it.
- vigo-home: `hostNetwork` for HomeKit mDNS. Its two replicas never share a node (they bind the same host ports); other HomeKit bridges such as homebridge and scrypted can share a node with it.
