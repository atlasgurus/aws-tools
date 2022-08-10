import sys

import boto3
import argparse

from util.vpc import is_nat_gateway_configured_for_internet_access
from util.output import pretty_print

ec2 = boto3.client("ec2")

DESCRIPTION = "Find private subnets with Nat Gateway attached and configured for internet access."


def find_vpc_private_subnets_with_nat_gateway_internet_access(vpc_id: str) -> list:
    result = []

    route_tables = ec2.describe_route_tables(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )

    for route_table in route_tables["RouteTables"]:
        if "Associations" in route_table:
            for route in route_table["Routes"]:
                if (
                    "DestinationCidrBlock" in route
                    and route["DestinationCidrBlock"] == "0.0.0.0/0"
                    and "NatGatewayId" in route
                    and is_nat_gateway_configured_for_internet_access(
                        route["NatGatewayId"], route_tables
                    )
                ):
                    for association in route_table["Associations"]:
                        if "SubnetId" in association:
                            result.append(association["SubnetId"])

    return result


def find_subnets(result: dict, vpcs: list) -> dict:
    result["VPC"] = []
    for vpc in vpcs:
        subnets = find_vpc_private_subnets_with_nat_gateway_internet_access(vpc)
        if len(subnets) > 0:
            result["VPC"].append({
                "VpcId": vpc,
                "Subnets": subnets
            })

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=DESCRIPTION
    )
    parser.add_argument("--vpcs", type=str, help="Comma-separated list of VPCs to search subnets in.", required=True)

    try:
        args = parser.parse_args()
    except AttributeError:
        parser.print_help()
        sys.exit(0)

    result = dict()
    result["Query"] = DESCRIPTION
    result = find_subnets(result, args.vpcs.split(","))
    pretty_print(result)


