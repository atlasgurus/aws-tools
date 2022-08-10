import argparse
import json
import sys

import boto3

from util.output import pretty_print
from util.vpc import is_vpc_endpoint_exists

ec2 = boto3.client("ec2")

INPUT_SCHEMA = {
    "VPC": [{
        "VpcId": "",
        "Subnets": []
    }]
}


def create_endpoint_security_group(
    vpc_id: str, subnets: list, service_name: str
) -> dict:
    security_group = ec2.create_security_group(
        Description=f"Allows connection to the VPC endpoint {service_name} from private subnets",
        GroupName=f"VPC-Endpoint-{service_name}",
        VpcId=vpc_id,
    )

    for subnet in subnets:
        subnets_desc = ec2.describe_subnets(SubnetIds=[subnet])
        if "Subnets" in subnets_desc and subnets_desc["Subnets"]:
            subnet_cidr = subnets_desc["Subnets"][0]["CidrBlock"]
            ec2.authorize_security_group_ingress(
                GroupId=security_group["GroupId"],
                IpProtocol="tcp",
                CidrIp=subnet_cidr,
                ToPort=443,
                FromPort=443,
            )

    return security_group


def create_vpc_endpoint(
    vpc_id: str, service_name: str, subnets: list
) -> list:
    result = []

    if is_vpc_endpoint_exists(vpc_id=vpc_id, service_name=service_name):
        print(
            f"Endpoint {service_name} already exists in VPC {vpc_id}. Skip endpoint creation."
        )
        return

    if subnets:
        security_group = create_endpoint_security_group(
            vpc_id, subnets, service_name
        )

        result.append({
            "Action": "Created security group",
            "Result": security_group
        })

        vpc_endpoint = ec2.create_vpc_endpoint(
            VpcEndpointType="Interface",
            VpcId=vpc_id,
            ServiceName=service_name,
            SubnetIds=subnets,
            SecurityGroupIds=[security_group["GroupId"]],
        )

        result.append({
            "Action": "Created VPC endpoint",
            "Result": vpc_endpoint["VpcEndpoint"]
        })

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create VPC endpoint for private subnets with NAT Gateway configured."
    )
    parser.add_argument(
        "--service-name",
        type=str,
        help="The name of AWS service to create a VPC endpoint for (for example, com.amazonaws.us-east-1.kms)",
        required=True
    )
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    args = parser.parse_args()

    input = json.load(sys.stdin)

    actions = []

    for vpc in input["VPC"]:
        if "VpcId" in vpc and "Subnets" in vpc:
            action = create_vpc_endpoint(
                vpc_id=vpc["VpcId"],
                service_name=args.service_name,
                subnets=vpc["Subnets"]
            )

            actions += action

    pretty_print(actions)
