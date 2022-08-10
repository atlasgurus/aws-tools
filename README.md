# AWS Find and Modify Tools

This project contains the set of Python utility scripts that allows to find AWS resources by certain attributes
and create new resources or modify existing.

## Script types
* **find_** scripts allows to find AWS resources. Produce JSON that can be passed to **create_** or **modify_** scripts.
* **create_** scripts ingest JSON produced by **find_** scripts and create new resources. Produce JSON that describes each action and created resource.
* **modify_** scripts ingest JSON produced by **find_** scripts and modify existing resources. Produce JSON that describes each action and modified resource.

## Usage
It's possible to pipe the output from one script to another. For example:

`python find_private_subnets_with_nat_gw_internet_access.py --vpcs vpc-12345 | python create_vpc_endpoints.py --service-name com.amazonaws.us-east-1.logs`