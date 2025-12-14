# democratic-csi

Per design, a single deployment can only manage a single storage class (see: [#446](https://github.com/democratic-csi/democratic-csi/issues/446)). As a result, to support multiple storage tiers in the same NAS instance, we create one deployment per tier.

At this moment, each deployment has a dedicated copy of helm based manifest generation setup. Deployments don't share any resource except for the namespace. As I am getting more familiar with the project, there might be opportunities to make some templating tricks to improve DRYness.

## Storage Classes

- `general-iscsi`: A RAIDZ2 pool with 6 HDDs of 7200RPM
