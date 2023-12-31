# Tandoor Recipes

Manifests are based on [the example in upstream repo](https://github.com/TandoorRecipes/recipes/tree/8d7b4f614cc61b11d96391a551f951bd6d2673bb/docs/install/k8s). Significant changes:

- Use an external HA postgres cluster, powered by [CloudNativePG](https://github.com/cloudnative-pg/cloudnative-pg).
- A bunch of sealed secrets.
- Double ingresses (LAN and Internet facing).
