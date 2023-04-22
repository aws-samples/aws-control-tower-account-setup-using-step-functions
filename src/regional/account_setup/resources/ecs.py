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

from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
import boto3
import botocore

if TYPE_CHECKING:
    from mypy_boto3_ecs import ECSClient

logger = Logger(child=True)

__all__ = ["ECS"]


class ECS:
    def __init__(self, session: boto3.Session, region: str) -> None:
        self.client: ECSClient = session.client("ecs", region_name=region)
        self.region = region

    def put_account_setting_default(self) -> None:
        names = [
            "serviceLongArnFormat",
            "taskLongArnFormat",
            "containerInstanceLongArnFormat",
            "awsvpcTrunking",
            "containerInsights",
            "dualStackIPv6",
        ]
        for name in names:
            try:
                self.client.put_account_setting_default(name=name, value="enabled")
            except botocore.exceptions.ClientError:
                logger.exception(f"Unable to enable ECS setting {name} in {self.region}")

        # documentation on https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-account-settings.html#tag-resources-setting is incorrect
        try:
            self.client.put_account_setting_default(name="tagResourceAuthorization", value="on")
        except botocore.exceptions.ClientError:
            logger.exception(f"Unable to enable ECS setting tagResourceAuthorization in {self.region}")
