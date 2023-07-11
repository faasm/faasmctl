## Deploy a Faasm cluster

Faasm supports being deployed on a [docker compose](#docker-compose) and on a
[k8s](#k8s) cluster.

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

In addition, you may set the WASM VM as an environment variable too. The
supported values are `WASM_VM=[wavm,wamr,sgx,sgx-sim]`.

Lastly, in order to delete a cluster, you may run:

```bash
faasmctl deploy.delete [--ini-file=<path_to_ini_file>]
```
