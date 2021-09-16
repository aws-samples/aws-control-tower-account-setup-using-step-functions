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

from functools import lru_cache
from typing import Optional, Dict, Any

from aws_lambda_powertools import Logger
import boto3
import botocore

__all__ = ["SSO"]

logger = Logger(child=True)


class SSO:
    def __init__(self, session: boto3.Session) -> None:
        self.client = session.client("sso-admin")
        self._permission_sets = {}
        self._instances = []

    def list_instances(self) -> Dict[str, str]:
        if self._instances:
            return self._instances

        instances = []
        paginator = self.client.get_paginator("list_instances")
        page_iterator = paginator.paginate()
        for page in page_iterator:
            instances.extend(page.get("Instances", []))

        self._instances = instances
        return instances

    def list_permission_sets(self, instance_arn: str) -> Dict[str, str]:
        if instance_arn in self._permission_sets:
            return self._permission_sets[instance_arn]

        permission_sets = {}

        paginator = self.client.get_paginator("list_permission_sets")
        page_iterator = paginator.paginate(InstanceArn=instance_arn)
        for page in page_iterator:
            for permission_set_arn in page.get("PermissionSets", []):

                response = self.client.describe_permission_set(
                    InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
                )

                name = response["PermissionSet"]["Name"]
                permission_sets[name] = permission_set_arn

        self._permission_sets[instance_arn] = permission_sets

        return permission_sets

    @lru_cache
    def get_permission_set_arn(self, instance_arn: str, name: str) -> Optional[str]:
        permission_sets = self.list_permission_sets(instance_arn)
        return permission_sets.get(name)

    def create_account_assignment(
        self,
        account_id: str,
        instance_arn: str,
        permission_set_arn: str,
        principal_id: str,
    ) -> Dict[str, Any]:
        try:
            response = self.client.create_account_assignment(
                InstanceArn=instance_arn,
                TargetId=account_id,
                TargetType="AWS_ACCOUNT",
                PermissionSetArn=permission_set_arn,
                PrincipalType="GROUP",
                PrincipalId=principal_id,
            )
            return response["AccountAssignmentCreationStatus"]
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] != "ConflictException":
                logger.exception(
                    f"Unable to add {permission_set_arn} to {principal_id} in {account_id}"
                )
                raise error

    def delete_account_assignment(
        self,
        account_id: str,
        instance_arn: str,
        permission_set_arn: str,
        principal_id: str,
    ) -> Dict[str, Any]:
        try:
            response = self.client.delete_account_assignment(
                InstanceArn=instance_arn,
                TargetId=account_id,
                TargetType="AWS_ACCOUNT",
                PermissionSetArn=permission_set_arn,
                PrincipalType="GROUP",
                PrincipalId=principal_id,
            )
            return response["AccountAssignmentDeletionStatus"]
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                logger.exception(
                    f"Unable to delete {permission_set_arn} from {principal_id} in {account_id}"
                )
                raise error
