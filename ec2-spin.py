import configparser
import boto3
import json
import time
import datetime
import argparse
import sys, os
from botocore.exceptions import ClientError



VERBOSE = True


def log(msg):
    if VERBOSE:
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {msg}")

# Define AWS credentials and region
config = configparser.ConfigParser()
config.read('/Users/brunosan/.aws/credentials')
aws_access_key_id = config.get('default', 'aws_access_key_id')
aws_secret_access_key = config.get('default', 'aws_secret_access_key')
config.read('/Users/brunosan/.aws/config')
region = config.get('default', 'region')

# Define EC2 instance parameters
instance_type = 't2.micro'
ami_id = 'ami-0557a15b87f6559cf'
key_name = 'wbAgS2KN'
security_group_name = 'wbAgS2SG'
username = 'ubuntu'

def cleanup_resources(resources):
    ec2 = boto3.client('ec2', region_name=region)

    try:
        # Detach the EBS volume from the instance if it's in use
        volume_id = resources['volume_id']
        instance_id = resources['instance_id']
        response = ec2.describe_volumes(VolumeIds=[volume_id])
        volume_state = response['Volumes'][0]['State']
        if volume_state == 'in-use':
            ec2.detach_volume(VolumeId=volume_id, InstanceId=instance_id, Force=True)
            log(f"Detaching volume {volume_id} from instance {instance_id}...")
            ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
            log(f"Volume {volume_id} successfully detached.")
        elif volume_state == 'available':
            log(f"Volume {volume_id} is already in the available state.")
    except Exception as e:
        log(f"Error cleaning up volume : {e}")

    # Delete the EBS volume
    try:
        ec2.delete_volume(VolumeId=volume_id)
        log(f"Deleted volume {volume_id}.")
    except Exception as e:
        log(f"Error deleting volume: {e}")

    # Terminate the EC2 instance
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        log(f"Terminating instance {instance_id}...")
        ec2.get_waiter('instance_terminated').wait(InstanceIds=[instance_id])
        log(f"Instance {instance_id} successfully terminated.")
    except Exception as e:
        log(f"Error terminating instance: {e}")

    # Delete the key pair
    try:
        ec2.delete_key_pair(KeyName=key_name)
        log(f"Deleted key pair {key_name}.")
        os.remove(key_name+'.rsa')
        log(f"Deleted private key file {key_name}.rsa")

    except Exception as e:
        log(f"Error deleting key pair: {e}")

    try:
        # Delete the security group
        security_group_id = resources['security_group_id']
        ec2.delete_security_group(GroupId=security_group_id)
        log(f"Deleted security group {security_group_id}.")
    except Exception as e:
        log(f"Error deleting security group: {e}")

    # Delete the subnet and VPC if they were created
    if resources.get('subnet_id') and resources.get('vpc_id'):
        subnet_id = resources['subnet_id']
        vpc_id = resources['vpc_id']
        try:
            ec2.delete_subnet(SubnetId=subnet_id)
            log(f"Deleted subnet {subnet_id}.")
            ec2.delete_vpc(VpcId=vpc_id)
            log(f"Deleted VPC {vpc_id}.")
        except Exception as e:
            log(f"Error deleting subnet or VPC: {e}")

    # Delete the resource file
    try:
        os.remove('deployed-resources.json')
        log("Deleted resource file deployed-resources.json.")
    except Exception as e:
        log(f"Error deleting resource file deployed-resources.json: {e}")



def deploy():
    try:
        # Create EC2 client
        log("Creating EC2 client...")
        ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key, region_name=region)

        try:
            # Check if key pair already exists
            response = ec2.describe_key_pairs(KeyNames=[key_name])
            if 'KeyPairs' in response and len(response['KeyPairs']) > 0:
                log("Key pair already exists.")
            else:
                raise ClientError({'Error': {'Code': 'InvalidKeyPair.NotFound'}})
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                log("Creating key pair...")
                # Create new key pair
                response = ec2.create_key_pair(KeyName=key_name)
                # Save private key to file
                with open(key_name+'.rsa', 'w') as f:
                    f.write(response['KeyMaterial'])
            else:
                log("Unexpected error: {}".format(e))

        # Check if security group already exists
        response = ec2.describe_security_groups()
        if 'SecurityGroups' in response and len(response['SecurityGroups']) > 0:
            log("Security group already exists.")
            security_group_id = response['SecurityGroups'][0]['GroupId']
        else:
            log("Creating security group...")

        subnet_id = None
        # Get default VPC ID
        response = ec2.describe_vpcs()
        if 'Vpcs' in response and len(response['Vpcs']) > 0:
            vpc_id = response['Vpcs'][0]['VpcId']
        else:
            log("No default VPC found. Creating new VPC...")
            # Create new VPC
            response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
            vpc_id = response['Vpc']['VpcId']
            # Modify VPC attributes
            ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
            ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
            # Create an Internet Gateway
            response = ec2.create_internet_gateway()
            internet_gateway_id = response['InternetGateway']['InternetGatewayId']
            # Attach the Internet Gateway to the VPC
            ec2.attach_internet_gateway(InternetGatewayId=internet_gateway_id, VpcId=vpc_id)
        #get or create subnet
        response = ec2.describe_subnets()
        if 'Subnets' in response and len(response['Subnets']) > 0:
            subnet_id = response['Subnets'][0]['SubnetId']
        else:
            log("No subnet found. Creating new subnet...")
            # Create new subnet
            response = ec2.create_subnet(CidrBlock='10.0.1.0/24', VpcId=vpc_id)
            subnet_id = response['Subnet']['SubnetId']

        # Create new security group
        response = ec2.create_security_group(
            GroupName=security_group_name, Description='Security group for WB Ag S2', VpcId=vpc_id)
        security_group_id = response['GroupId']
        # Authorize inbound traffic
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )

        log("Creating EC2 instance...")
        # Launch EC2 instance
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[security_group_id],
            SubnetId=subnet_id,
            MaxCount=1,
            MinCount=1
        )
        # Get instance ID
        instance_id = response['Instances'][0]['InstanceId']

        # Wait for instance to be running
        log('Waiting for instance to be running...')
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])

        instance_desc = ec2.describe_instances(InstanceIds=[instance_id])
        instance_az = instance_desc['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']


        # Create EBS volume
        response = ec2.create_volume(
            AvailabilityZone=instance_az,
            Size=10,
        )

        # Get volume ID
        volume_id = response['VolumeId']

        # Wait for volume to be available
        log('Waiting for volume to be available...')
        ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])

        # Attach volume to instance
        ec2.attach_volume(
            Device='/dev/xvdf',
            InstanceId=instance_id,
            VolumeId=volume_id,
        )

        # Wait for volume to be attached
        log('Waiting for volume to be attached...')
        time.sleep(10)

        # Assuming you have already created an EC2 resource object named 'ec2'
        existing_ips = ec2.describe_addresses(Filters=[{'Name': 'domain', 'Values': ['vpc']}])['Addresses']
        if existing_ips:
            # Use the first available IP address
            elastic_ip = existing_ips[0]['PublicIp']
            response = ec2.associate_address(InstanceId=instance_id, PublicIp=elastic_ip)
            log(f"Associated Elastic IP address {elastic_ip} with instance {response['AssociationId']}")
        else:
            log("No available Elastic IP addresses found")
            # Allocate a new Elastic IP address
            response = ec2.allocate_address(Domain='vpc')
            elastic_ip = response['PublicIp']
            log(f"Allocated Elastic IP address: {elastic_ip}")

        # Associate the Elastic IP address with the instance
        response = ec2.associate_address(InstanceId=instance_id, PublicIp=elastic_ip)
        log(f"Associated Elastic IP address {elastic_ip} with instance {instance_id}")


        # Get the public IP address
        public_ip = None
        while public_ip is None:
            log('Waiting for public IP address...')
            time.sleep(5)  # Wait for 5 seconds before checking again
            instance_desc = ec2.describe_instances(InstanceIds=[instance_id])
            public_ip = instance_desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        log(f"SSH command: ssh -i {key_name}.rsa {username}@{public_ip}")

        # Save variables to a file
        variables = {}
        for k in ['instance_id', 'volume_id', 'security_group_id', 
                  'internet_gateway_id','subnet_id', 'vpc_id', 'public_ip', 
                  'elastic_ip', 'username']:
            if k in locals():
                variables[k] = locals()[k]
        with open('deployed-resources.json', 'w') as f:
            json.dump(variables, f)

    except Exception as e:
        log(f"Error: {e}")
        resources={}
        for k in ['instance_id', 'volume_id', 'security_group_id', 'internet_gateway_id', 
                  'subnet_id', 'vpc_id']:
            if k in locals():
                resources[k] = locals()[k]
        cleanup_resources(resources)
        raise
    finally:
        # Save variables to a file
        variables = {}
        for k in ['instance_id', 'volume_id', 'security_group_id', 'internet_gateway_id', 
                  'subnet_id', 'vpc_id','elastic_ip', 'public_ip', 'username', 'key_name']:
            if k in locals():
                variables[k] = locals()[k]
        with open('deployed-resources.json', 'w') as f:
            json.dump(variables, f)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy or clean up resources.')
    parser.add_argument('action', choices=['deploy', 'cleanup'], help='Choose the action to perform: deploy or cleanup.')

    args = parser.parse_args()

    if args.action == 'deploy':
        #check if the file 'deployed-resources.json' exists
        if os.path.exists('deployed-resources.json'):
            log("File 'deployed-resources.json' already exists. Please clean up deployment before running this script again.")
            log("E.g. run 'python deploy.py cleanup' to clean up resources.")
            sys.exit(1)
        else:
            deploy()
    elif args.action == 'cleanup':
        #check if the file 'deployed-resources.json' exists
        if not os.path.exists('deployed-resources.json'):
            log("File 'deployed-resources.json' does not exist. Can't cleanup automatically, or no previous deployment exists.")
            sys.exit(1)
        with open('deployed-resources.json', 'r') as f:
            resources = json.load(f)
        cleanup_resources(resources)
