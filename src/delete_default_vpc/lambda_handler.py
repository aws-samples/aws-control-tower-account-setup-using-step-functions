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

# see https://github.com/awslabs/aws-deployment-framework/blob/master/src/lambda_codebase/initial_commit/bootstrap_repository/adf-build/provisioner/src/vpc.py

from concurrent.futures import ThreadPoolExecutor
import os
import time
from typing import Dict, Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import botocore

EXECUTION_ROLE_NAME = os.environ["EXECUTION_ROLE_NAME"]
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def vpc_cleanup(vpcid: str, session: boto3.Session, region: str) -> None:
    if not vpcid:
        return

    ec2 = session.resource("ec2", region_name=region)
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)

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

    # Delete vpc
    ec2client.delete_vpc(VpcId=vpcid)
    logger.info(f"VPC {vpcid} and associated resources has been deleted.")


@tracer.capture_method
def delete_default_vpc(
    client: Any, account_id: str, region: str, session: boto3.Session
) -> None:
    default_vpc_id = None
    max_retry_seconds = 360
    while True:
        try:
            vpc_response = client.describe_vpcs()
            break
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "OptInRequired":
                logger.warning(
                    f"Passing on region {client.meta.region_name} as Opt-in is required."
                )
                return
        except BaseException as error:
            logger.warning(
                f"Could not retrieve VPCs: {error}. Sleeping for 2 seconds before trying again."
            )
            max_retry_seconds = +2
            time.sleep(2)
            if max_retry_seconds <= 0:
                raise Exception("Could not describe VPCs within retry limit.")

    for vpc in vpc_response["Vpcs"]:
        if vpc["IsDefault"] is True:
            default_vpc_id = vpc["VpcId"]
            break

    if default_vpc_id is None:
        logger.debug(
            f"No default VPC found in account {account_id} in the {region} region"
        )
        return

    logger.info(f"Found default VPC Id {default_vpc_id} in the {region} region")
    vpc_cleanup(default_vpc_id, session, region)


@tracer.capture_method
def schedule_delete_default_vpc(
    account_id: str, region: str, credentials: Dict[str, str]
) -> None:
    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
    ec2_client = session.client("ec2", region_name=region)
    delete_default_vpc(ec2_client, account_id, region, session)


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    account_id = event.get("account", {}).get("accountId")
    if not account_id:
        raise Exception("Account ID not found in event")

    session = boto3.Session()
    ec2 = session.client("ec2")

    all_regions = [
        region["RegionName"]
        for region in ec2.describe_regions(
            Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required"]}],
            AllRegions=False,
        )["Regions"]
    ]

    sts = session.client("sts")

    role_arn = f"arn:aws:iam::{account_id}:role/{EXECUTION_ROLE_NAME}"
    credentials = sts.assume_role(
        RoleArn=role_arn, RoleSessionName="delete_default_vpc"
    )["Credentials"]

    args = ((account_id, region, credentials) for region in all_regions)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for _ in executor.map(lambda f: schedule_delete_default_vpc(*f), args):
            pass
