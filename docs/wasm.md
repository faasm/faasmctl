## Uploading WASM functions to a running cluster

In order to execute a WASM function in a Faasm cluster, we need to upload it
first. Functions in Faasm are identified by a `(user, function)` pair. In order
to upload a function, you may run:

```bash
faasmctl upload <user> <func> --wasm-file <path_to_file.wasm>
```

to invoke the function, check out the [invocation](invoke.md) docs.

Note that Faasm uses a custom host interface that extends WASI, so we recommend
cross-compiling C/C++ functions with our custom [toolchain](
https://github.com/faasm/cpp).

If your function expects files to be present in Faasm's filesystem, you can
also upload them by running:

```bash
faasmctl upload.file --host-path <path_to_file> --faasm-path <path_in_wasm>
```

then, your C/C++ function will be able to access the file at
`faasm://path_in_wasm`.
