#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
* SPDX-License-Identifier: MIT-0
*
* Permission is hereby granted, free of charge, to any person obtaining a copy of this
* software and associated documentation files (the "Software"), to deal in the Software
* without restriction, including without limitation the rights to use, copy, modify,
* merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
* INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
* PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
* HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
* OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from typing import Optional

from aws_lambda_powertools import Logger
import boto3

logger = Logger(child=True)

__all__ = ["EC2"]


class EC2:
    def __init__(self, session: boto3.Session, region: str) -> None:
        self.client = session.client("ec2", region_name=region)
        self.session = session
        self.region_name = region

    def get_default_vpc_id(self) -> Optional[str]:
        params = {"Filters": [{"Name": "isDefault", "Values": ["true"]}]}

        response = self.client.describe_vpcs(**params)
        for vpc in response.get("Vpcs", []):
            if vpc["IsDefault"]:
                return vpc["VpcId"]

        logger.debug("No default VPC found")
        return None

    def delete_vpc(self, vpc_id: str) -> None:
        ec2 = self.session.resource("ec2", region_name=self.region_name)
        vpc = ec2.Vpc(vpc_id)

        # detach and delete all gateways associated with the vpc
        for gw in vpc.internet_gateways.all():
            vpc.detach_internet_gateway(InternetGatewayId=gw.id)
            gw.delete()

        # Route table associations
        for rt in vpc.route_tables.all():
            for rta in rt.associations:
                if not rta.main:
                    rta.delete()

        # Security Group
        for sg in vpc.security_groups.all():
            if sg.group_name != "default":
                sg.delete()

        # Network interfaces
        for subnet in vpc.subnets.all():
            for interface in subnet.network_interfaces.all():
                interface.delete()
            subnet.delete()

        # Network ACLs
        for nacl in vpc.network_acls.all():
            if not nacl.is_default:
                nacl.delete()

        # DHCP Options
        if vpc.dhcp_options:
            vpc.associate_dhcp_options(
                DhcpOptionsId="default"
            )  # associate no DHCP options
            vpc.dhcp_options.delete()

        # Delete VPC
        self.client.delete_vpc(VpcId=vpc_id)
        logger.info(f"VPC {vpc_id} and associated resources has been deleted.")

    def enable_ebs_encryption_by_default(self):
        self.client.enable_ebs_encryption_by_default()
