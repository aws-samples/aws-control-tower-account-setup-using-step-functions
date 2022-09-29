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

from typing import Dict

import boto3

__all__ = ["IdentityStore"]


class IdentityStore:
    def __init__(self, session: boto3.Session, identity_store_id: str) -> None:
        self.client = session.client("identitystore")
        self._identity_store_id = identity_store_id

    def get_groups_by_prefix(self, prefix: str) -> Dict[str, str]:
        """
        Return all of the groups that match a given prefix
        """
        paginator = self.client.get_paginator("list_groups")
        page_iterator = paginator.paginate(
            IdentityStoreId=self._identity_store_id,
            PaginationConfig={
                "PageSize": 100,
            },
        )

        groups: Dict[str, str] = {}
        for page in page_iterator:
            for group in page.get("Groups", []):
                if group["DisplayName"].startswith(prefix):
                    groups[group["GroupId"]] = group["DisplayName"]

        return groups
