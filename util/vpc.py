import boto3

ec2 = boto3.client("ec2")


def is_vpc_endpoint_exists(vpc_id: str, service_name: str) -> bool:
    resp = ec2.describe_vpc_endpoints(
        Filters=[
            {"Name": "service-name", "Values": [service_name]},
            {"Name": "vpc-id", "Values": [vpc_id]},
            {
                "Name": "vpc-endpoint-state",
                "Values": ["available"],
            },
        ]
    )

    return "VpcEndpoints" in resp and len(resp["VpcEndpoints"]) > 0


def is_nat_gateway_configured_for_internet_access(
    nat_gw_id: str, route_tables: dict
) -> bool:
    nat_gateways = ec2.describe_nat_gateways(
        NatGatewayIds=[
            nat_gw_id,
        ]
    )

    if "NatGateways" in nat_gateways:
        nat_gw = nat_gateways["NatGateways"][0]
        if nat_gw["ConnectivityType"] == "public":
            nat_gw_subnet = nat_gw["SubnetId"]
            for route_table in route_tables["RouteTables"]:
                if "Associations" in route_table:
                    for association in route_table["Associations"]:
                        if "SubnetId" in association and association["SubnetId"] == nat_gw_subnet:
                            for route in route_table["Routes"]:
                                if (
                                    "DestinationCidrBlock" in route
                                    and route["DestinationCidrBlock"] == "0.0.0.0/0"
                                    and "GatewayId" in route
                                ):
                                    return True

    return False
