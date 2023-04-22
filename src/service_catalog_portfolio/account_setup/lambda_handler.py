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
from typing import Dict, Any, List, Optional

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from .resources import IAM, ServiceCatalog, STS

tracer = Tracer()
logger = Logger()


def get_env_list(key: str) -> List[str]:
    """
    Return an optional environment variable as a list
    """
    value = os.environ.get(key, "").split(",")
    return list(filter(None, value))


PORTFOLIO_IDS = get_env_list("PORTFOLIO_IDS")
PERMISSION_SET_NAMES = get_env_list("PERMISSION_SET_NAMES")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    account_id: Optional[str] = event.get("account", {}).get("accountId")
    if not account_id:
        raise Exception("Account ID not found in event")

    session = STS().assume_role(account_id, "service_catalog_portfolio")

    iam = IAM(session)

    role_arns = set()

    for permission_set_name in PERMISSION_SET_NAMES:
        role_arn = iam.get_role_arn(permission_set_name)
        if role_arn:
            role_arns.add(role_arn)

    servicecatalog = ServiceCatalog(session)

    for portfolio_id in PORTFOLIO_IDS:
        servicecatalog.accept_portfolio_share(portfolio_id)

        existing_principals = servicecatalog.list_principals_for_portfolio(portfolio_id)

        to_add = role_arns - existing_principals
        to_remove = existing_principals - role_arns

        for role_arn in to_add:
            servicecatalog.associate_principal_with_portfolio(portfolio_id=portfolio_id, principal_arn=role_arn)

        for role_arn in to_remove:
            servicecatalog.disassociate_principal_from_portfolio(portfolio_id=portfolio_id, principal_arn=role_arn)
