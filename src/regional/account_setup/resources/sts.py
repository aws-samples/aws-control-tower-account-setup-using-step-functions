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

import os

from aws_lambda_powertools import Logger
import boto3

logger = Logger(child=True)
EXECUTION_ROLE_NAME = os.environ["EXECUTION_ROLE_NAME"]
AWS_PARTITION = os.environ["AWS_PARTITION"]

__all__ = ["STS"]


class STS:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("sts")

    def assume_role(
        self, account_id: str, role_session_name: str = "AccountSetup"
    ) -> boto3.Session:
        """
        Assume the AWSControlTowerExecution role in an account
        """

        role_arn = f"arn:{AWS_PARTITION}:iam::{account_id}:role/{EXECUTION_ROLE_NAME}"

        logger.info(f"Assuming role {EXECUTION_ROLE_NAME} in {account_id}")
        response = self.client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            DurationSeconds=900,  # shortest duration 15 minutes
        )

        credentials = response["Credentials"]

        return boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )
