from faasmctl.util.config import get_faasm_ini_value, update_faasm_ini_value
from faasmctl.util.deploy import generate_ini_file
from os import environ, listdir
from os.path import expanduser, join
from subprocess import run
from time import sleep

DEFAULT_KUBECONFIG_PATH = join(expanduser("~"), ".kube", "config")
BASE_LABEL = "faasm.io/role"
CONTROL_LABEL = "{}=control".format(BASE_LABEL)
WORKER_LABEL = "{}=worker".format(BASE_LABEL)


def run_k8s_cmd(k8s_config, namespace, cmd, capture_output=False):
    k8s_cmd = [
        "kubectl",
        "--kubeconfig {}".format(k8s_config),
        "-n {}".format(namespace) if namespace else "",
        cmd,
    ]
    k8s_cmd = " ".join(k8s_cmd)

    if capture_output:
        return run(k8s_cmd, shell=True, capture_output=True).stdout.decode("utf-8")

    run(k8s_cmd, shell=True, check=True)


def get_k8s_env_vars(k8s_context, faasm_checkout, workers):
    env = {}

    env["K8S_KUBECONFIG_FILE"] = k8s_context
    env["K8S_NAMESPACE"] = "faasm"

    env["K8S_COMMON_DIR"] = join(faasm_checkout, "deploy", "k8s-common")
    env["K8S_SGX_DIR"] = join(faasm_checkout, "deploy", "k8s-sgx")
    env["K8S_WAVM_DIR"] = join(faasm_checkout, "deploy", "k8s")
    env["K8S_WAMR_DIR"] = join(faasm_checkout, "deploy", "k8s-wamr")
    env["K8S_NAMESPACE_FILE"] = join(env["K8S_COMMON_DIR"], "namespace.yml")

    env["FAASM_NUM_WORKERS"] = workers

    # Whitelist env. variables that we recognise
    if "FAASM_WASM_VM" in environ:
        env["FAASM_WASM_VM"] = environ["FAASM_WASM_VM"]
    else:
        env["FAASM_WASM_VM"] = "wamr"

    return env


def get_k8s_nodes(k8s_context):
    out = run_k8s_cmd(k8s_context, None, "get nodes", capture_output=True).strip()
    nodes = [node.split(" ")[0] for node in out.split("\n")][1:]

    return nodes


def label_k8s_nodes(k8s_context, num_workers):
    """
    This method labels the nodes in the K8s cluster for a Faasm deployment.

    One node will get the control label, meaning that it will run all the
    non-worker pods. The other nodes will get the worker label, meaning that
    each one will run one worker pod (per node!).
    """
    # First, assert that we have at least workers + 1 nodes in the K8s cluster
    k8s_nodes = get_k8s_nodes(k8s_context)
    if len(k8s_nodes) < (num_workers + 1):
        print(
            "Not enough nodes in the K8s cluster (have: {} - need: {})".format(
                len(k8s_nodes), num_workers + 1
            )
        )
        raise RuntimeError("Not enough nodes in the K8s cluster!")

    # Second, label 1 node as control, and #worker nodes as workers
    def label_node(node, label):
        run_k8s_cmd(
            k8s_context,
            None,
            "label nodes {} {}".format(node, label),
            capture_output=True,
        )

    label_node(k8s_nodes[0], CONTROL_LABEL)
    for i in range(1, num_workers + 1):
        label_node(k8s_nodes[i], WORKER_LABEL)


def deploy_k8s_cluster(k8s_context, faasm_checkout, workers, ini_file):
    """
    Deploy a docker compose cluster

    Parameters:
    - faasm_checkout (str): path to the Faasm's source code checkout
    - workers (int): number of workers to deploy
    - mount_source (bool): flag to indicate whether we mount code/binaries
    - ini_file (str): path to the ini_file to generate (if selected)

    Returns:
    - (str): path to the generated ini_file
    """
    # Before deploying, label the cluster nodes accordingly
    label_k8s_nodes(k8s_context, workers)

    env = get_k8s_env_vars(k8s_context, faasm_checkout, workers)

    deploy_faasm_services(env)

    # Once deployed, gather all the information necessary to generate the INI
    # file
    invoke_ip, invoke_port = get_lb_ip_port(env, "worker-lb")
    upload_ip, upload_port = get_lb_ip_port(env, "upload-lb")
    planner_ip, planner_port = get_lb_ip_port(env, "planner-lb")
    worker_names, worker_ips = get_faasm_worker_pods(env, "run=faasm-worker")

    # Finally, generate the faasm.ini file to interact with the cluster
    return generate_ini_file(
        "k8s",
        out_file=ini_file,
        cwd=faasm_checkout,
        k8s_config=env["K8S_KUBECONFIG_FILE"],
        k8s_namespace=env["K8S_NAMESPACE"],
        upload_ip=upload_ip,
        upload_port=upload_port,
        planner_ip=planner_ip,
        planner_port=planner_port,
        worker_names=worker_names,
        worker_ips=worker_ips,
    )


def deploy_faasm_services(env):
    """
    Main entrypoint to deploy all the components of a Faasm k8s cluster
    """
    # ----------
    # Deploy all different services and deployments
    # ----------

    # Set up the namespace first
    run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        None,
        "apply -f {}".format(env["K8S_NAMESPACE_FILE"]),
    )

    # First, add all the common files
    k8s_files = [
        join(env["K8S_COMMON_DIR"], f)
        for f in listdir(env["K8S_COMMON_DIR"])
        if f.endswith(".yml")
    ]

    # Then add the deployment specific files
    if env["FAASM_WASM_VM"] == "sgx":
        k8s_dir = env["K8S_SGX_DIR"]
    elif env["FAASM_WASM_VM"] == "wamr":
        k8s_dir = env["K8S_WAMR_DIR"]
    elif env["FAASM_WASM_VM"] == "wavm":
        k8s_dir = env["K8S_WAVM_DIR"]
    else:
        print("Unrecognised WASM VM: {}".format(env["FAASM_WASM_VM"]))
        raise RuntimeError("Unrecognised WASM VM")
    k8s_files += [join(k8s_dir, f) for f in listdir(k8s_dir) if f.endswith(".yml")]

    # Apply all the files
    print("Applying k8s files: {}".format(k8s_files))
    for file_path in k8s_files:
        run_k8s_cmd(
            env["K8S_KUBECONFIG_FILE"],
            None,
            "apply -f {}".format(file_path),
        )

    # ----------
    # Wait for services
    # ----------

    # Wait for faasm services
    wait_for_faasm_pods(env, "app=faasm")

    # Wait for the worker deployment
    wait_for_faasm_pods(env, "run=faasm-worker")

    # ----------
    # Scale the worker deployment and wait
    # ----------

    run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        env["K8S_NAMESPACE"],
        "scale deployment/faasm-worker --replicas={}".format(env["FAASM_NUM_WORKERS"]),
    )
    wait_for_faasm_pods(env, "run=faasm-worker")

    # ----------
    # Wait for the LBs to be assigned ingress IPs
    # ----------

    wait_for_faasm_lb(env, "worker-lb")
    wait_for_faasm_lb(env, "planner-lb")
    wait_for_faasm_lb(env, "upload-lb")


def get_faasm_worker_pods(env, label):
    # To get pods with STATUS "Running" (not "Terminating") we need to use this
    # long template. There's a long-going open discussion on GH about it:
    # https://github.com/kubernetes/kubectl/issues/450
    cmd = [
        "get pods",
        "-l {}".format(label),
        """--template "{{range .items}}{{ if not .metadata.deletionTimestamp"""
        """ }}{{.metadata.name}}{{'\\n'}}{{end}}{{end}}" """,
    ]
    output = run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        env["K8S_NAMESPACE"],
        " ".join(cmd),
        capture_output=True,
    )
    names = ["faasm" + o.strip("10") for o in output.split("faasm") if o.strip()]

    # Now get the pod IPs
    cmd = [
        "get pods",
        "-l {}".format(label),
        """--template "{{range .items}}{{ if not .metadata.deletionTimestamp"""
        """ }}{{.status.podIP}}:{{end}}{{end}}" """,
    ]
    output = run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        env["K8S_NAMESPACE"],
        " ".join(cmd),
        capture_output=True,
    )
    ips = [o.strip() for o in output.split(":") if o.strip()]

    return names, ips


def get_lb_ip_port(env, lb_name):
    """
    Get the ingress IP and port for a load balancer service
    """
    ip = run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        env["K8S_NAMESPACE"],
        " ".join(
            [
                "get service {}".format(lb_name),
                "-o 'jsonpath={.status.loadBalancer.ingress[0].ip}'",
            ]
        ),
        capture_output=True,
    )

    port = run_k8s_cmd(
        env["K8S_KUBECONFIG_FILE"],
        env["K8S_NAMESPACE"],
        " ".join(
            [
                "get service {}".format(lb_name),
                "-o 'jsonpath={.spec.ports[0].port}'",
            ]
        ),
        capture_output=True,
    )

    return ip, port


def wait_for_faasm_pods(env, label):
    # Wait for the faasm pods to be ready
    while True:
        print("Waiting for Faasm pods...")
        cmd = [
            "get pods -l {}".format(label),
            "-o jsonpath='{..status.conditions[?(@.type==\"Ready\")].status}'",
        ]

        output = run_k8s_cmd(
            env["K8S_KUBECONFIG_FILE"],
            env["K8S_NAMESPACE"],
            " ".join(cmd),
            capture_output=True,
        )

        statuses = [o.strip() for o in output.split(" ") if o.strip()]
        if all([s == "True" for s in statuses]):
            print("All Faasm pods ready, continuing...")
            break

        true_statuses = len([s for s in statuses if s == "True"])
        print(
            "Faasm pods not ready, waiting ({}/{})".format(true_statuses, len(statuses))
        )
        sleep(5)


def wait_for_faasm_lb(env, service_name):
    """
    Wait for load balancers to be assigned an ingress IP
    """
    while True:
        print("Waiting for ingress IPs to be assigned")
        cmd = [
            "get service {}".format(service_name),
            "-o jsonpath='{.status.loadBalancer.ingress[0].ip}'",
        ]

        output = run_k8s_cmd(
            env["K8S_KUBECONFIG_FILE"],
            env["K8S_NAMESPACE"],
            " ".join(cmd),
            capture_output=True,
        )

        if output != "":
            print("Load balancer ({}) ready".format(service_name))
            break

        print("Load balancer ({}) not ready".format(service_name))
        sleep(5)


def delete_k8s_cluster(ini_file):
    """
    Delete a cluster running on k8s

    Parameters:
    - ini_file (str): path to the ini_file generated by the deploy command
    """
    working_dir = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    k8s_config = get_faasm_ini_value(ini_file, "Faasm", "k8s_config")

    # We don't care about the number of workers when deleting, so we can pass
    # a zero
    env = get_k8s_env_vars(k8s_config, working_dir, 0)

    for dir_to_delete in [
        env["K8S_COMMON_DIR"],
        env["K8S_WAVM_DIR"],
        env["K8S_WAMR_DIR"],
        env["K8S_SGX_DIR"],
    ]:
        run_k8s_cmd(
            k8s_config,
            None,
            "delete --all -f {}".format(dir_to_delete),
        )


def restart_pod_by_name(ini_file, pod_names):
    k8s_config = get_faasm_ini_value(ini_file, "Faasm", "k8s_config")
    faasm_checkout = get_faasm_ini_value(ini_file, "Faasm", "working_dir")
    env = get_k8s_env_vars(k8s_config, faasm_checkout, 0)

    run_k8s_cmd(
        k8s_config,
        "faasm",
        "delete pod {}".format(" ".join(pod_names)),
        capture_output=True,
    )

    # Update the worker list
    worker_names, worker_ips = get_faasm_worker_pods(env, "run=faasm-worker")

    update_faasm_ini_value(ini_file, "Faasm", "worker_names", ",".join(worker_names))
    update_faasm_ini_value(ini_file, "Faasm", "worker_ips", ",".join(worker_ips))
