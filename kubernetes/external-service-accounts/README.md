# Service accounts used from outside the cluster

## kubenav

[kubenav](https://github.com/kubenav/kubenav) is a mobile app. It includes many help functionalities like deploying stuff with a click of button. But I am not going to use that since everything should be GitOps.

This account allows me to use kubenav as a read-only client. It should not have permission to modify anything in the cluster.
