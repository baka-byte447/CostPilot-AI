from kubernetes import client, config


def scale_deployment(deployment_name, namespace, replicas):

    config.load_kube_config()

    api = client.AppsV1Api()

    body = {
        "spec": {
            "replicas": replicas
        }
    }

    api.patch_namespaced_deployment_scale(
        name=deployment_name,
        namespace=namespace,
        body=body
    )

    return {
        "deployment": deployment_name,
        "new_replicas": replicas
    }