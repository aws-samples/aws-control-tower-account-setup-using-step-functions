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

from account_setup.resources import IAM, STS, S3, CloudWatchLogs
from account_setup.schemas import INPUT

tracer = Tracer()
logger = Logger()


@validator(inbound_schema=INPUT)
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    account_id = event["account"]["accountId"]

    logger.append_keys(account_id=account_id)

    session = boto3.Session()

    assumed_session = STS(session).assume_role(account_id)

    logger.info("Updating IAM password policy")
    iam = IAM(assumed_session)
    iam.update_account_password_policy()

    logger.info("Blocking public S3 buckets")
    s3 = S3(assumed_session)
    s3.put_public_access_block(account_id)

    logger.info(
        "Creating CloudWatch Logs resource policy to allow Route 53 query logging in us-east-1"
    )
    logs = CloudWatchLogs(assumed_session)
    logs.put_resource_policy(account_id)
