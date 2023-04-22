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
from typing import Optional, Dict, TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_iam import IAMClient

__all__ = ["IAM"]

AWS_SSO_ROLE_PREFIX = "AWSReservedSSO_"


class IAM:
    def __init__(self, session: Optional[boto3.Session] = None) -> None:
        if not session:
            session = boto3._get_default_session()
        self.client: IAMClient = session.client("iam")
        self._roles: Dict[str, str] = {}

    def get_sso_roles(self) -> Dict[str, str]:
        """
        Get the list of AWS SSO permission set role ARNs organized by the permission set name
        """
        if self._roles:
            return self._roles

        roles = {}
        paginator = self.client.get_paginator("list_roles")
        page_iterator = paginator.paginate(PaginationConfig={"PageSize": 1000})
        for page in page_iterator:
            for role in page.get("Roles", []):
                if role["RoleName"].startswith(AWS_SSO_ROLE_PREFIX):
                    # AWSReservedSSO_AWSAdministratorAccess_a1ff75f56dfb0e2f -> AWSAdministratorAccess
                    permission_set_name = role["RoleName"].rsplit("_", 1)[0].replace(AWS_SSO_ROLE_PREFIX, "")
                    roles[permission_set_name] = role["Arn"]

        self._roles = roles

        return roles

    @lru_cache
    def get_role_arn(self, permission_set_name: str) -> Optional[str]:
        roles = self.get_sso_roles()
        return roles.get(permission_set_name)
