## FaasmCTL API

To programatically interact with a Faasm cluster, or to use more advanced (or
custom) features than those included in the command line tasks (`faasmctl -l`),
we recommend using the `faasmctl` API.

After installing `faasmctl` as a python dependency, you may import any of the
functions defined in [`faasmctl.util`](./faasmctl/util/). For an example on how
to use the API, you may see how we upload and invoke functions in the
[CPP repo](https://github.com/faasm/cpp/tree/main/tasks/func.py).
