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

from concurrent.futures import ThreadPoolExecutor
import os
from typing import Dict, Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3

EXECUTION_ROLE_NAME = os.environ["EXECUTION_ROLE_NAME"]
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def schedule_ecs_account_settings(region: str, credentials: Dict[str, str]) -> None:
    # create a new session per region
    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
    client = session.client("ecs", region_name=region)

    names = [
        "serviceLongArnFormat",
        "taskLongArnFormat",
        "containerInstanceLongArnFormat",
        "awsvpcTrunking",
        "containerInsights",
        # "dualStackIPv6", # not yet supported
    ]
    for name in names:
        client.put_account_setting_default(name=name, value="enabled")


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
    logger.info(f"Discovered regions: {all_regions}")

    sts = session.client("sts")

    role_arn = f"arn:aws:iam::{account_id}:role/{EXECUTION_ROLE_NAME}"
    credentials = sts.assume_role(
        RoleArn=role_arn, RoleSessionName="ecs_account_settings"
    )["Credentials"]

    args = ((region, credentials) for region in all_regions)

    with ThreadPoolExecutor(max_workers=10) as executor:
        for _ in executor.map(lambda f: schedule_ecs_account_settings(*f), args):
            pass
