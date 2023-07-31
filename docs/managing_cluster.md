## Managing a Faasm cluster

Before reading how to manage a Faasm cluster, make sure you have read the doc
on how to [deploy a Faasm cluster](./deploy.md).

### Monitor and debug a cluster

The instructions to monitor and debug a cluster apply mostly to `compose`
clusters. `kubernetes` clusters are harder to interact with, and we recommend
using a special-purpose `k8s` monitoring tool. We strongly recommend [`k9s`](
https://github.com/derailed/k9s).

To get the status of the running services in the cluster you may run:

```bash
faasmctl status
```

To get the logs of a number of running services you may run:

```bash
faasmctl logs -s upload [-s worker, -s <another>] [-f,--follow]
```

the `--follow` flag attaches to the logs.

To restart a running service you may run:

```bash
faasmctl restart -s upload [-s worker, -s <another>]
```

### Delete a cluster

Lastly, in order to delete a cluster, you may run:

```bash
faasmctl deploy.delete
```

