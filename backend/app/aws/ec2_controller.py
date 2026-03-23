import logging

from .aws_client import aws

logger = logging.getLogger(__name__)

class EC2Controller:
    def get_asg_info(self, asg_name: str) -> dict:
        """Returns current state of an Auto Scaling Group."""
        resp = aws.autoscaling().describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        groups = resp.get("AutoScalingGroups", [])
        if not groups:
            raise ValueError(f"ASG '{asg_name}' not found")
        g = groups[0]
        return {
            "name": g["AutoScalingGroupName"],
            "desired": g["DesiredCapacity"],
            "min": g["MinSize"],
            "max": g["MaxSize"],
            "instances": len(g["Instances"]),
            "healthy": sum(1 for i in g["Instances"] if i["HealthStatus"] == "Healthy"),
        }

    def set_desired_capacity(self, asg_name: str, desired: int) -> dict:
        """
        Core scaling action: set desired instance count on an ASG.
        The RL agent calls this after deciding scale_up or scale_down.
        """
        info = self.get_asg_info(asg_name)

        # Clamp to ASG min/max so we never violate hard limits
        desired = max(info["min"], min(info["max"], desired))

        if desired == info["desired"]:
            logger.info(f"ASG {asg_name}: already at desired={desired}, no change")
            return {"action": "no_change", "desired": desired}

        aws.autoscaling().set_desired_capacity(
            AutoScalingGroupName=asg_name,
            DesiredCapacity=desired,
            HonorCooldown=True  # Respect the ASG cooldown period
        )
        direction = "scale_up" if desired > info["desired"] else "scale_down"
        logger.info(f"ASG {asg_name}: {direction} {info['desired']}→{desired}")
        return {
            "action": direction,
            "previous": info["desired"],
            "desired": desired,
            "asg": asg_name
        }

    def scale_up(self, asg_name: str, increment: int = 1) -> dict:
        """Add `increment` instances to the ASG."""
        info = self.get_asg_info(asg_name)
        return self.set_desired_capacity(asg_name, info["desired"] + increment)

    def scale_down(self, asg_name: str, decrement: int = 1) -> dict:
        """Remove `decrement` instances from the ASG."""
        info = self.get_asg_info(asg_name)
        return self.set_desired_capacity(asg_name, info["desired"] - decrement)

    def terminate_idle_instances(self, asg_name: str, cpu_threshold: float = 5.0) -> dict:
        """
        Finds instances in the ASG with CPU below threshold (idle)
        and terminates them, letting the ASG decide replacement.
        This is what saves money on truly idle boxes.
        """
        cw = aws.cloudwatch()
        asg_info = self.get_asg_info(asg_name)

        resp = aws.autoscaling().describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        instances = resp["AutoScalingGroups"][0]["Instances"]
        idle = []

        for inst in instances:
            instance_id = inst["InstanceId"]
            # Pull last 10 minutes of CPU from CloudWatch
            metrics = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                Period=600,
                StartTime=__import__("datetime").datetime.utcnow() - __import__("datetime").timedelta(minutes=10),
                EndTime=__import__("datetime").datetime.utcnow(),
                Statistics=["Average"]
            )
            datapoints = metrics.get("Datapoints", [])
            if datapoints:
                avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)
                if avg_cpu < cpu_threshold:
                    idle.append(instance_id)

        terminated = []
        for instance_id in idle:
            # decrement_desired=True tells ASG to shrink, not replace
            aws.autoscaling().terminate_instance_in_auto_scaling_group(
                InstanceId=instance_id,
                ShouldDecrementDesiredCapacity=True
            )
            terminated.append(instance_id)
            logger.info(f"Terminated idle instance {instance_id} from {asg_name}")

        return {
            "action": "terminate_idle",
            "asg": asg_name,
            "checked": len(instances),
            "terminated": terminated,
            "count": len(terminated)
        }

    def change_instance_type(self, instance_id: str, new_type: str) -> dict:
        """
        Changes the instance type of a STOPPED EC2 instance.
        NOTE: The instance must be stopped first — we handle that here.
        Use this for right-sizing decisions (e.g. t3.micro → t3.medium).
        """
        ec2 = aws.ec2()

        # Stop the instance
        logger.info(f"Stopping {instance_id} to change type to {new_type}")
        ec2.stop_instances(InstanceIds=[instance_id])

        # Wait until stopped (blocks — consider making async for production)
        waiter = ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[instance_id])

        # Change type
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={"Value": new_type}
        )

        # Restart
        ec2.start_instances(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} restarted as {new_type}")

        return {
            "action": "change_instance_type",
            "instance_id": instance_id,
            "new_type": new_type
        }

    def list_asgs(self) -> list:
        """List all Auto Scaling Groups in the account/region."""
        resp = aws.autoscaling().describe_auto_scaling_groups()
        return [
            {
                "name": g["AutoScalingGroupName"],
                "desired": g["DesiredCapacity"],
                "min": g["MinSize"],
                "max": g["MaxSize"],
                "instances": len(g["Instances"])
            }
            for g in resp.get("AutoScalingGroups", [])
        ]