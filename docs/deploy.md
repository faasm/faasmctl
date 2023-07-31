## Deploy a Faasm cluster

Faasm supports being deployed on a [docker compose](#docker-compose) and on a
[k8s](#kubernetes) cluster.

### INI Files

As a consequence of a correct deployment, `faasmctl` generates an INI file.
The default location of the INI file is in the directory where
`faasmctl deploy` is called, and is named: `faasm.ini`. All subsequent
interactions with the running cluster require passing the INI file either as
an argument, or setting an environment variable:

```bash
# In general, we need to pass the `--ini-file` flag
faasmctl deploy.delete --ini-file ./faasm.ini

# Unless we set an env. variable
export FAASM_INI_FILE=./faasm.ini

# Then we do not need an ini file
faasmctl deploy.delete
```

### Environment Variables

In addition to the `FAASM_INI_FILE` environment variable, there are other
environment variables that you can set before starting a Faasm cluster to
influence the cluster creation process:
* `WASM_VM=[wavm,wamr,sgx,sgx-sim]`: set the WASM VM of choice.
* `FAASM_VERSION`: set the Faasm version to use (i.e. [version tag](
https://github.com/faasm/faasm/tags).

### Docker Compose

To deploy on a docker compose, make sure you have both `docker` and
`docker compose` installed (not `docker-compose`).

Then, you may run:

```bash
faasmctl deploy.compose \
    --ini-file=<ini_file_path> (default: ./faasm.ini) \
    --workers=<num_workers> (default: 2) \
    --mount-source=<path_to_local_checkout> (default: None) \
    [--clean]
```

The `--workers` argument indicates the number of workers to start in the cluster.
The `--mount-source` argument indicates a local checkout of Faasm's source code
to mount into the compose cluster. This means that we mount both the code
and built binaries.
The `--clean` flag erases any cached checkouts of the source code used
internally by `faasmctl`.

> WARNING: The `--clean` flag and the `--dev` flag are incompatible, as it
> could lead to accidentally removing user code.

### Kubernetes

To deploy Faasm on a Kubernetes cluster, you will have to first start a K8s
cluster yourself, and keep track of the generated `KUBECONFIG` file. For
example, for most of Faasm deployments we use Azure's Kubernetes Service.
You may see find the scripts to deploy such a cluster [here](
https://github.com/faasm/experiment-base/tree/main/tasks/cluster.py).

Then, you may run:

```bash
faasmctl deploy.k8s \
  --workers <num_workers> \
  --context <path to KUBECONFIG file> \
  --ini-file <out path for INI file>
```

if the `--context` flag is not set, `faasmctl` will check for the `KUBECONFIG`
environment variable, and if that is not set neither will look for a config
file in `~/.kube/config`.

### Managing a running cluster

For further steps on managing a running cluster, check [this page](
./managing_cluster.md).
