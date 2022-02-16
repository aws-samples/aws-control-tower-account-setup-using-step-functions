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

from typing import Dict, Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator
import boto3

from account_setup.resources import EC2, ECS, STS, SSM
from account_setup.schemas import INPUT

tracer = Tracer()
logger = Logger()


@validator(inbound_schema=INPUT)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    account_id = event["account_id"]
    region_name = event["region"]

    logger.append_keys(account_id=account_id, region=region_name)

    session = boto3.Session()

    assumed_session = STS(session).assume_role(account_id)

    logger.info("Deleting default VPC")
    ec2 = EC2(assumed_session, region_name)
    default_vpc_id = ec2.get_default_vpc_id()
    if default_vpc_id:
        ec2.delete_vpc(default_vpc_id)

    logger.info("Setting default ECS settings")
    ecs = ECS(assumed_session, region_name)
    ecs.put_account_setting_default()

    logger.info("Enabling EBS encryption by default")
    ec2.enable_ebs_encryption_by_default()

    logger.info("Blocking SSM documents from being made public")
    ssm = SSM(assumed_session, region_name, account_id)
    ssm.update_service_setting()
