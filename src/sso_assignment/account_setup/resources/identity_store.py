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
from typing import Optional

import boto3

__all__ = ["IdentityStore"]


class IdentityStore:
    def __init__(self, session: boto3.Session, identity_store_id: str) -> None:
        self.client = session.client("identitystore")
        self._identity_store_id = identity_store_id

    @lru_cache
    def get_group_id(self, name: str) -> Optional[str]:
        response = self.client.list_groups(
            IdentityStoreId=self._identity_store_id,
            Filters=[{"AttributePath": "DisplayName", "AttributeValue": name}],
        )
        for group in response.get("Groups", []):
            return group["GroupId"]

        return None

    def clear_groups(self) -> None:
        self.get_group_id.cache_clear()
