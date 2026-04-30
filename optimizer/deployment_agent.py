import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from config import AWS_REGION

logger = logging.getLogger(__name__)


def apply_actions(actions):
    """Apply optimization actions via AWS APIs."""
    results = []
    if not actions:
        return results

    ec2_clients = {}
    rds_clients = {}

    for action in actions:
        region = action.get("region") or AWS_REGION
        r_type = action.get("resource_type") or "Unknown"
        action_name = action.get("action")
        resource_id = action.get("resource_id")
        parameters = action.get("parameters") or {}

        if parameters.get("manual_only"):
            results.append(
                {
                    "action_id": action.get("id"),
                    "resource_id": resource_id,
                    "status": "skipped",
                    "message": "manual review required",
                    "applied_at": datetime.utcnow().isoformat(),
                }
            )
            continue

        try:
            if r_type == "EC2":
                ec2 = ec2_clients.get(region)
                if ec2 is None:
                    ec2 = boto3.client("ec2", region_name=region)
                    ec2_clients[region] = ec2
                result = _apply_ec2_action(ec2, action_name, resource_id, parameters)
            elif r_type == "RDS":
                rds = rds_clients.get(region)
                if rds is None:
                    rds = boto3.client("rds", region_name=region)
                    rds_clients[region] = rds
                result = _apply_rds_action(rds, action_name, resource_id)
            elif r_type == "EBS":
                ec2 = ec2_clients.get(region)
                if ec2 is None:
                    ec2 = boto3.client("ec2", region_name=region)
                    ec2_clients[region] = ec2
                result = _apply_ebs_action(ec2, action_name, resource_id)
            elif r_type in ("ElasticIP", "EIP"):
                ec2 = ec2_clients.get(region)
                if ec2 is None:
                    ec2 = boto3.client("ec2", region_name=region)
                    ec2_clients[region] = ec2
                result = _apply_eip_action(ec2, action_name, resource_id)
            elif r_type == "Snapshot":
                ec2 = ec2_clients.get(region)
                if ec2 is None:
                    ec2 = boto3.client("ec2", region_name=region)
                    ec2_clients[region] = ec2
                result = _apply_snapshot_action(ec2, action_name, resource_id)
            else:
                result = _skip_result("unsupported resource type")

        except ClientError as e:
            error = e.response.get("Error", {})
            result = _fail_result("AWS error %s: %s" % (error.get("Code"), error.get("Message")))
        except Exception as e:
            result = _fail_result(str(e))

        results.append(
            {
                "action_id": action.get("id"),
                "resource_id": resource_id,
                "status": result["status"],
                "message": result["message"],
                "applied_at": datetime.utcnow().isoformat(),
            }
        )

    return results


def _apply_ec2_action(ec2, action, instance_id, parameters):
    if action == "maintain":
        return _skip_result("maintain decision - no action required")
    state = _get_instance_state(ec2, instance_id)
    if action == "stop":
        if state == "stopped":
            return _skip_result("instance already stopped")
        ec2.stop_instances(InstanceIds=[instance_id])
        return _ok_result("stop requested")
    if action == "start":
        if state == "running":
            return _skip_result("instance already running")
        ec2.start_instances(InstanceIds=[instance_id])
        return _ok_result("start requested")
    if action == "restart":
        if state != "running":
            return _skip_result("instance not running")
        ec2.reboot_instances(InstanceIds=[instance_id])
        return _ok_result("reboot requested")
    if action == "delete":
        ec2.terminate_instances(InstanceIds=[instance_id])
        return _ok_result("terminate requested")
    if action == "resize":
        return _resize_ec2_instance(ec2, instance_id, parameters)
    return _skip_result("unsupported EC2 action")


def _resize_ec2_instance(ec2, instance_id, parameters):
    new_type = parameters.get("to_type")
    if not new_type:
        return _skip_result("missing target instance type")

    state = _get_instance_state(ec2, instance_id)
    was_running = state == "running"

    if state not in ("stopped", "stopping"):
        ec2.stop_instances(InstanceIds=[instance_id])
        waiter = ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[instance_id])

    ec2.modify_instance_attribute(InstanceId=instance_id, InstanceType={"Value": new_type})

    if parameters.get("restart", True) and was_running:
        ec2.start_instances(InstanceIds=[instance_id])

    return _ok_result("resize to %s requested" % new_type)


def _apply_rds_action(rds, action, db_id):
    if action == "maintain":
        return _skip_result("maintain decision - no action required")
    if action == "stop":
        rds.stop_db_instance(DBInstanceIdentifier=db_id)
        return _ok_result("stop requested")
    if action == "start":
        rds.start_db_instance(DBInstanceIdentifier=db_id)
        return _ok_result("start requested")
    if action == "restart":
        rds.reboot_db_instance(DBInstanceIdentifier=db_id)
        return _ok_result("reboot requested")
    if action == "delete":
        rds.delete_db_instance(DBInstanceIdentifier=db_id, SkipFinalSnapshot=True)
        return _ok_result("delete requested")
    return _skip_result("unsupported RDS action")


def _apply_ebs_action(ec2, action, volume_id):
    if action == "delete":
        ec2.delete_volume(VolumeId=volume_id)
        return _ok_result("delete requested")
    return _skip_result("unsupported EBS action")


def _apply_eip_action(ec2, action, public_ip):
    if action != "delete":
        return _skip_result("unsupported EIP action")

    response = ec2.describe_addresses(PublicIps=[public_ip])
    addresses = response.get("Addresses", [])
    if not addresses:
        return _skip_result("elastic IP not found")

    allocation_id = addresses[0].get("AllocationId")
    if allocation_id:
        ec2.release_address(AllocationId=allocation_id)
    else:
        ec2.release_address(PublicIp=public_ip)

    return _ok_result("release requested")


def _apply_snapshot_action(ec2, action, snapshot_id):
    if action == "delete":
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        return _ok_result("delete requested")
    return _skip_result("unsupported snapshot action")


def _ok_result(message):
    return {"status": "applied", "message": message}


def _skip_result(message):
    return {"status": "skipped", "message": message}


def _fail_result(message):
    return {"status": "failed", "message": message}


def _get_instance_state(ec2, instance_id):
    try:
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        for reservation in resp.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                return inst.get("State", {}).get("Name", "unknown")
    except Exception:
        return "unknown"
    return "unknown"
