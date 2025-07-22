import pulumi
import pulumi_aws as aws
import logging
from typing import Optional, Dict, List
import json

# Configure logging for auditing and debugging
logging.basicConfig(
    filename='pulumi_deployment.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VPC:
    """Class to manage a custom AWS VPC."""
    def __init__(self, name: str, cidr_block: str, provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.vpc = aws.ec2.Vpc(
                name,
                cidr_block=cidr_block,
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created VPC: {name}")
        except Exception as e:
            logger.error(f"Failed to create VPC {name}: {str(e)}")
            raise

    def get_vpc_id(self) -> pulumi.Output[str]:
        return self.vpc.id

class Subnet:
    """Class to manage subnets within a VPC."""
    def __init__(self, name: str, vpc_id: pulumi.Output[str], cidr_block: str, availability_zone: str, provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.subnet = aws.ec2.Subnet(
                name,
                vpc_id=vpc_id,
                cidr_block=cidr_block,
                availability_zone=availability_zone,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created subnet: {name}")
        except Exception as e:
            logger.error(f"Failed to create subnet {name}: {str(e)}")
            raise

    def get_subnet_id(self) -> pulumi.Output[str]:
        return self.subnet.id

class SecurityGroup:
    """Class to manage a security group."""
    def __init__(self, name: str, vpc_id: pulumi.Output[str], rules: List[Dict], provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.security_group = aws.ec2.SecurityGroup(
                name,
                vpc_id=vpc_id,
                description=f"Security group for {name}",
                ingress=rules,
                egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created security group: {name}")
        except Exception as e:
            logger.error(f"Failed to create security group {name}: {str(e)}")
            raise

    def get_security_group_id(self) -> pulumi.Output[str]:
        return self.security_group.id

class S3Bucket:
    """Class to manage an AWS S3 bucket for static content."""
    def __init__(self, name: str, is_public: bool = False, provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.bucket = aws.s3.Bucket(
                name,
                acl="public-read" if is_public else "private",
                website={"index_document": "index.html"} if is_public else None,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            if is_public:
                self.bucket_policy = aws.s3.BucketPolicy(
                    f"{name}-policy",
                    bucket=self.bucket.id,
                    policy=self.bucket.id.apply(lambda id: json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{id}/*"
                        }]
                    })),
                    opts=pulumi.ResourceOptions(provider=provider)
                )
            logger.info(f"Created S3 bucket: {name}")
        except Exception as e:
            logger.error(f"Failed to create S3 bucket {name}: {str(e)}")
            raise

    def get_bucket_arn(self) -> pulumi.Output[str]:
        return self.bucket.arn

    def get_bucket_name(self) -> str:
        return self.name

class EC2Instance:
    """Class to manage an AWS EC2 instance."""
    def __init__(self, name: str, instance_type: str, ami_id: str, subnet_id: pulumi.Output[str], security_group_ids: List[pulumi.Output[str]], provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.instance = aws.ec2.Instance(
                name,
                instance_type=instance_type,
                ami=ami_id,
                subnet_id=subnet_id,
                vpc_security_group_ids=security_group_ids,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created EC2 instance: {name}")
        except Exception as e:
            logger.error(f"Failed to create EC2 instance {name}: {str(e)}")
            raise

    def get_instance_id(self) -> pulumi.Output[str]:
        return self.instance.id

    def get_public_ip(self) -> pulumi.Output[str]:
        return self.instance.public_ip

class AutoScalingGroup:
    """Class to manage an Auto Scaling group."""
    def __init__(self, name: str, launch_template_id: pulumi.Output[str], subnet_ids: List[pulumi.Output[str]], min_size: int, max_size: int, desired_capacity: int, provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.asg = aws.autoscaling.Group(
                name,
                launch_template={"id": launch_template_id},
                min_size=min_size,
                max_size=max_size,
                desired_capacity=desired_capacity,
                vpc_zone_identifier=subnet_ids,
                tags=[{"key": "Environment", "value": "dev", "propagate_at_launch": True}, {"key": "Name", "value": name, "propagate_at_launch": True}],
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created Auto Scaling group: {name}")
        except Exception as e:
            logger.error(f"Failed to create Auto Scaling group {name}: {str(e)}")
            raise

    def get_asg_name(self) -> pulumi.Output[str]:
        return self.asg.name

class RDSInstance:
    """Class to manage an AWS RDS PostgreSQL instance."""
    def __init__(self, name: str, instance_class: str, db_name: str, username: str, password: str, subnet_ids: List[pulumi.Output[str]], security_group_ids: List[pulumi.Output[str]], provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.db_subnet_group = aws.rds.SubnetGroup(
                f"{name}-subnet-group",
                subnet_ids=subnet_ids,
                tags={"Environment": "dev", "Name": f"{name}-subnet-group"},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            self.rds = aws.rds.Instance(
                name,
                instance_class=instance_class,
                allocated_storage=20,
                engine="postgres",
                engine_version="13.7",
                db_name=db_name,
                username=username,
                password=password,
                vpc_security_group_ids=security_group_ids,
                db_subnet_group_name=self.db_subnet_group.name,
                multi_az=True,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created RDS instance: {name}")
        except Exception as e:
            logger.error(f"Failed to create RDS instance {name}: {str(e)}")
            raise

    def get_endpoint(self) -> pulumi.Output[str]:
        return self.rds.endpoint

class LoadBalancer:
    """Class to manage an Application Load Balancer."""
    def __init__(self, name: str, subnet_ids: List[pulumi.Output[str]], security_group_ids: List[pulumi.Output[str]], provider: Optional[aws.Provider] = None):
        self.name = name
        try:
            self.alb = aws.lb.LoadBalancer(
                name,
                internal=False,
                load_balancer_type="application",
                subnets=subnet_ids,
                security_groups=security_group_ids,
                tags={"Environment": "dev", "Name": name},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            self.target_group = aws.lb.TargetGroup(
                f"{name}-tg",
                port=80,
                protocol="HTTP",
                vpc_id=subnet_ids[0].apply(lambda id: aws.ec2.get_subnet(id=id).vpc_id),
                target_type="instance",
                health_check={"path": "/", "protocol": "HTTP"},
                tags={"Environment": "dev", "Name": f"{name}-tg"},
                opts=pulumi.ResourceOptions(provider=provider)
            )
            self.listener = aws.lb.Listener(
                f"{name}-listener",
                load_balancer_arn=self.alb.arn,
                port=80,
                protocol="HTTP",
                default_actions=[{"type": "forward", "target_group_arn": self.target_group.arn}],
                opts=pulumi.ResourceOptions(provider=provider)
            )
            logger.info(f"Created ALB: {name}")
        except Exception as e:
            logger.error(f"Failed to create ALB {name}: {str(e)}")
            raise

    def get_dns_name(self) -> pulumi.Output[str]:
        return self.alb.dns_name

def get_latest_ami(region: str) -> str:
    """Retrieve the latest Amazon Linux 2 AMI ID for the specified region."""
    try:
        ami = aws.ec2.get_ami(
            most_recent=True,
            filters=[
                aws.ec2.GetAmiFilterArgs(name="name", values=["amzn2-ami-hvm-*-x86_64-gp2"]),
                aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["amazon"])
            ]
        )
        logger.info(f"Retrieved AMI ID: {ami.id} for region {region}")
        return ami.id
    except Exception as e:
        logger.error(f"Failed to retrieve AMI ID for region {region}: {str(e)}")
        raise

def main():
    """Main function to deploy an enterprise-scale AWS infrastructure."""
    try:
        # Load Pulumi configuration
        config = pulumi.Config()
        region = config.get("aws:region") or "us-east-1"
        instance_type = config.get("instance_type") or "t2.micro"
        bucket_name = config.get("bucket_name") or "my-app-bucket-2025"
        db_name = config.get("db_name") or "myappdb"
        db_username = config.get_secret("db_username") or "admin"
        db_password = config.get_secret("db_password") or "securepassword123"  # Use secrets in production
        min_size = config.get_int("min_size") or 2
        max_size = config.get_int("max_size") or 4
        desired_capacity = config.get_int("desired_capacity") or 2

        # Configure AWS provider
        aws_provider = aws.Provider(
            "aws-provider",
            region=region
        )

        # Create VPC
        vpc = VPC("my-app-vpc", "10.0.0.0/16", provider=aws_provider)

        # Create subnets
        subnets = [
            Subnet("subnet-1", vpc.get_vpc_id(), "10.0.1.0/24", f"{region}a", provider=aws_provider),
            Subnet("subnet-2", vpc.get_vpc_id(), "10.0.2.0/24", f"{region}b", provider=aws_provider)
        ]
        subnet_ids = [subnet.get_subnet_id() for subnet in subnets]

        # Create security groups
        web_sg = SecurityGroup(
            "web-sg",
            vpc.get_vpc_id(),
            [
                {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
                {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}
            ],
            provider=aws_provider
        )
        db_sg = SecurityGroup(
            "db-sg",
            vpc.get_vpc_id(),
            [{"protocol": "tcp", "from_port": 5432, "to_port": 5432, "cidr_blocks": ["10.0.0.0/16"]}],
            provider=aws_provider
        )

        # Create S3 bucket for static content
        s3_bucket = S3Bucket(bucket_name, is_public=True, provider=aws_provider)

        # Retrieve latest AMI
        ami_id = get_latest_ami(region)

        # Create launch template for Auto Scaling
        launch_template = aws.ec2.LaunchTemplate(
            "app-launch-template",
            image_id=ami_id,
            instance_type=instance_type,
            vpc_security_group_ids=[web_sg.get_security_group_id()],
            tags={"Environment": "dev", "Name": "app-launch-template"},
            opts=pulumi.ResourceOptions(provider=aws_provider)
        )

        # Create Auto Scaling group
        asg = AutoScalingGroup(
            "app-asg",
            launch_template.id,
            subnet_ids,
            min_size,
            max_size,
            desired_capacity,
            provider=aws_provider
        )

        # Create RDS instance
        rds = RDSInstance(
            "app-db",
            "db.t3.micro",
            db_name,
            db_username,
            db_password,
            subnet_ids,
            [db_sg.get_security_group_id()],
            provider=aws_provider
        )

        # Create Application Load Balancer
        alb = LoadBalancer("app-alb", subnet_ids, [web_sg.get_security_group_id()], provider=aws_provider)

        # Export outputs
        pulumi.export("vpc_id", vpc.get_vpc_id())
        pulumi.export("subnet_ids", subnet_ids)
        pulumi.export("bucket_name", s3_bucket.get_bucket_name())
        pulumi.export("bucket_arn", s3_bucket.get_bucket_arn())
        pulumi.export("asg_name", asg.get_asg_name())
        pulumi.export("db_endpoint", rds.get_endpoint())
        pulumi.export("alb_dns_name", alb.get_dns_name())
        logger.info("Enterprise deployment completed successfully")

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()