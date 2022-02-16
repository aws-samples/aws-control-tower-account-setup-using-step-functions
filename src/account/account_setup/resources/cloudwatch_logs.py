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

import json

from aws_lambda_powertools import Tracer
import boto3

tracer = Tracer()
__all__ = ["CloudWatchLogs"]


class CloudWatchLogs:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("logs", region_name="us-east-1")

    @tracer.capture_method
    def put_resource_policy(self, account_id: str) -> None:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Route53LogsToCloudWatchLogs",
                    "Effect": "Allow",
                    "Principal": {"Service": "route53.amazonaws.com"},
                    "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                    "Resource": f"arn:aws:logs:us-east-1:{account_id}:log-group:/aws/route53/*",  # log-group must be in us-east-1
                }
            ],
        }

        self.client.put_resource_policy(
            policyName="AWSServiceRoleForRoute53", policyDocument=json.dumps(policy)
        )
