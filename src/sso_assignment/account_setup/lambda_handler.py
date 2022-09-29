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
import boto3

from .resources import Organizations, IdentityStore, SSO
from .utils import parse_group
from .constants import GROUP_ORG_PREFIX

tracer = Tracer()
logger = Logger()


@tracer.capture_method(capture_response=False)
def create_group_event(event: Dict[str, Any]) -> None:
    """
    Assign the new group to an account and permission set
    """
    group = event.get("responseElements", {}).get("group", {})
    if not group:
        logger.warn("No group found in event")
        return

    group_id = group["groupId"]
    group_name = group["groupName"]

    try:
        account_name, permission_set_name = parse_group(group_name)
    except Exception as error:
        logger.warn(error)
        return

    if not account_name:
        logger.warn(f"Unrecognized account group name: {group_name}")
        return

    session = boto3.Session()
    organizations = Organizations(session)
    account_id = organizations.get_account_id(account_name)
    if not account_id:
        logger.warn(f"No account named '{account_name}'")
        return

    sso = SSO(session)

    permission_set_arn = None
    instances = sso.list_instances()

    for instance in instances:
        instance_arn = instance["InstanceArn"]

        permission_set_arn = sso.get_permission_set_arn(
            instance_arn=instance_arn, name=permission_set_name
        )
        if permission_set_arn:
            logger.info(
                f"Assigning {group_name} permission set {permission_set_name} in {account_id}"
            )
            sso.create_account_assignment(
                account_id=account_id,
                instance_arn=instance_arn,
                permission_set_arn=permission_set_arn,
                principal_id=group_id,
            )
            break

    if not permission_set_arn:
        logger.warn(f"Permission Set '{permission_set_name}' not found")


@tracer.capture_lambda_handler(capture_response=False)
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    # Handle single-account groups
    if event.get("eventName") == "CreateGroup":
        return create_group_event(event)

    # Below handles organizational groups

    account_id = event.get("account", {}).get("accountId")
    if not account_id:
        raise Exception("Account ID not found in event")

    logger.info(f"Assigning organizational groups to account {account_id}")

    session = boto3.Session()
    sso = SSO(session)

    instances = sso.list_instances()
    for instance in instances:
        instance_arn = instance["InstanceArn"]
        identity_store_id = instance["IdentityStoreId"]

        identity_store = IdentityStore(session, identity_store_id)
        organizational_groups = identity_store.get_groups_by_prefix(GROUP_ORG_PREFIX)

        for group_id, group_name in organizational_groups.items():
            _, permission_set_name = parse_group(group_name)

            permission_set_arn = sso.get_permission_set_arn(
                instance_arn=instance_arn, name=permission_set_name
            )
            if not permission_set_arn:
                logger.error(
                    f"Permission Set '{permission_set_name}' not found, skipping"
                )
                continue

            logger.info(
                f"Assigning {group_name} permission set {permission_set_name} in {account_id}"
            )
            sso.create_account_assignment(
                account_id=account_id,
                instance_arn=instance_arn,
                permission_set_arn=permission_set_arn,
                principal_id=group_id,
            )
