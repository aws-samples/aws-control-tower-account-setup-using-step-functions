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
from typing import Optional, Tuple, List

from .constants import GROUP_ACCOUNT_PREFIX, GROUP_ORG_PREFIX

__all__ = ["get_env_list", "parse_group"]


def get_env_list(key: str) -> List[str]:
    """
    Return an optional environment variable as a list
    """
    value = os.environ.get(key, "").split(",")
    return list(filter(None, value))


def parse_group(group_name: str) -> Tuple[Optional[str], str]:
    """
    Parse a group name into the account name and permission set name
    """
    account_name = None
    permission_set_name = None

    # AWS-A-AccountA-DeveloperAccess
    if group_name.startswith(GROUP_ACCOUNT_PREFIX):

        group_parts = group_name.replace(GROUP_ACCOUNT_PREFIX, "").rsplit("-", 1)
        account_name = group_parts[2]  # AccountA
        permission_set_name = group_parts[3]  # DeveloperAccess

    # AWS-O-AWSReadOnlyAccess
    elif group_name.startswith(GROUP_ORG_PREFIX):
        group_parts = group_name.split("-", 2)
        permission_set_name = group_parts[2]  # AWSReadOnlyAccess

    else:
        raise Exception(f"Unrecognized group name: {group_name}")

    return (account_name, permission_set_name)
