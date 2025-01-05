import boto3

# Parameters
VPC_ID = "vpc-0321f38a7b594180d"  # Replace with your VPC ID
SUBNET_IDS = [
    "subnet-06bd72b2e4cb41d10",
    "subnet-09bd0e0acc92d4efa",
]  # Replace with your subnet IDs
AMI_ID = "ami-04dd23e62ed049936"  # Replace with the correct AMI ID for your backend instances
INSTANCE_TYPE = "t3.medium"  # Choose an appropriate instance type
USER_DATA = """#!/bin/bash
# Update and install Docker
sudo apt update -y
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# ECR login
$(aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 975050024946.dkr.ecr.us-west-2.amazonaws.com)

# Pull the Docker images from ECR
docker pull 975050024946.dkr.ecr.us-west-2.amazonaws.com/pk1-a-repo:profile-service
docker pull 975050024946.dkr.ecr.us-west-2.amazonaws.com/pk1-a-repo:hello-service

# Run the Docker containers
docker run -d -p 3002:3002 975050024946.dkr.ecr.us-west-2.amazonaws.com/pk1-a-repo:profile-service
docker run -d -p 3001:3001 975050024946.dkr.ecr.us-west-2.amazonaws.com/pk1-a-repo:hello-service
"""

TARGET_GROUP_NAME = "pk1-backend-target-group"
LOAD_BALANCER_NAME = "pk1-my-alb"
AUTO_SCALING_GROUP_NAME = "pk1-backend-asg"

# Initialize Boto3 clients
ec2 = boto3.client("ec2")
elbv2 = boto3.client("elbv2")
autoscaling = boto3.client("autoscaling")

# 1. Create a new Security Group for the Load Balancer
security_group_response = ec2.create_security_group(
    GroupName="pk1-alb-sg1",  # Name of the security group
    Description="Security group for ALB",
    VpcId=VPC_ID,
)

security_group_id = security_group_response["GroupId"]

# Add an inbound rule to allow HTTP traffic on port 80 (this will be for the ALB)
ec2.authorize_security_group_ingress(
    GroupId=security_group_id,
    IpPermissions=[
        {
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],  # Allow from anywhere
        }
    ],
)

# 2. Create a Target Group for the Backend instances
target_group_response = elbv2.create_target_group(
    Name=TARGET_GROUP_NAME,
    Protocol="HTTP",
    Port=80,  # or whichever port your backend uses
    VpcId=VPC_ID,
    HealthCheckProtocol="HTTP",
    HealthCheckPort="80",
    HealthCheckPath="/health",  # Replace with your actual health check endpoint
    Matcher={
        "HttpCode": "200"  # Adjust this to match your backend health check response
    },
)

target_group_arn = target_group_response["TargetGroups"][0]["TargetGroupArn"]

# 3. Create an Application Load Balancer (ALB)
load_balancer_response = elbv2.create_load_balancer(
    Name=LOAD_BALANCER_NAME,
    Subnets=SUBNET_IDS,
    SecurityGroups=[security_group_id],  # Use the newly created security group
    Scheme="internet-facing",
    Type="application",
    IpAddressType="ipv4",
)

alb_arn = load_balancer_response["LoadBalancers"][0]["LoadBalancerArn"]
alb_dns_name = load_balancer_response["LoadBalancers"][0]["DNSName"]

# Modify the Load Balancer Attributes
elbv2.modify_load_balancer_attributes(
    LoadBalancerArn=alb_arn,
    Attributes=[{"Key": "idle_timeout.timeout_seconds", "Value": "60"}],
)

# 4. Create an Auto Scaling Group (ASG)
launch_configuration_response = autoscaling.create_launch_configuration(
    LaunchConfigurationName=f"{AUTO_SCALING_GROUP_NAME}-launch-config",
    ImageId=AMI_ID,
    InstanceType=INSTANCE_TYPE,
    SecurityGroups=[security_group_id],  # Ensure the correct SG is used for instances
    UserData=USER_DATA,
    InstanceMonitoring={"Enabled": True},
)

asg_response = autoscaling.create_auto_scaling_group(
    AutoScalingGroupName=AUTO_SCALING_GROUP_NAME,
    LaunchConfigurationName=f"{AUTO_SCALING_GROUP_NAME}-launch-config",
    MinSize=2,  # Minimum number of instances
    MaxSize=5,  # Maximum number of instances
    DesiredCapacity=2,  # Desired number of instances
    VPCZoneIdentifier=",".join(SUBNET_IDS),  # Replace with your subnet IDs
    TargetGroupARNs=[target_group_arn],  # Associate with the target group
    HealthCheckType="EC2",
    HealthCheckGracePeriod=300,  # Adjust this based on your health check needs
    Tags=[{"Key": "Name", "Value": "backend-instance", "PropagateAtLaunch": True}],
)

# 5. Register the ALB with Auto Scaling Group
# ALB Listener setup (HTTP Listener to forward traffic to the target group)
listener_response = elbv2.create_listener(
    LoadBalancerArn=alb_arn,
    Protocol="HTTP",
    Port=80,
    DefaultActions=[{"Type": "forward", "TargetGroupArn": target_group_arn}],
)

# Print the ALB DNS Name and confirmation of Auto Scaling Group creation
print(f"ALB DNS Name: {alb_dns_name}")
print(f"Auto Scaling Group {AUTO_SCALING_GROUP_NAME} created successfully.")
