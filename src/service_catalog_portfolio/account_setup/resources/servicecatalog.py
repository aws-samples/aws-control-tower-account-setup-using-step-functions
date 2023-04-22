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

from typing import Set, TYPE_CHECKING, Optional

from aws_lambda_powertools import Logger
import boto3
import botocore

if TYPE_CHECKING:
    from mypy_boto3_servicecatalog import ServiceCatalogClient, ListPrincipalsForPortfolioPaginator

logger = Logger(child=True)

__all__ = ["ServiceCatalog"]


class ServiceCatalog:
    def __init__(self, session: Optional[boto3.Session] = None) -> None:
        if not session:
            session = boto3._get_default_session()
        self.client: ServiceCatalogClient = session.client("servicecatalog")

    def accept_portfolio_share(self, portfolio_id: str) -> None:
        try:
            self.client.accept_portfolio_share(PortfolioId=portfolio_id, PortfolioShareType="AWS_ORGANIZATIONS")
        except botocore.exceptions.ClientError:
            logger.exception("Unable to accept portfolio share")
            raise

    def associate_principal_with_portfolio(self, portfolio_id: str, principal_arn: str) -> None:
        try:
            self.client.associate_principal_with_portfolio(
                PortfolioId=portfolio_id,
                PrincipalARN=principal_arn,
                PrincipalType="IAM",
            )
        except botocore.exceptions.ClientError:
            logger.exception("Unable to associate princpal with portfolio")
            raise

    def disassociate_principal_from_portfolio(self, portfolio_id: str, principal_arn: str) -> None:
        try:
            self.client.disassociate_principal_from_portfolio(PortfolioId=portfolio_id, PrincipalARN=principal_arn)
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                logger.exception("Unable to disassociate princpal from portfolio")
                raise

    def list_principals_for_portfolio(self, portfolio_id: str) -> Set[str]:
        principals = set()

        paginator: ListPrincipalsForPortfolioPaginator = self.client.get_paginator("list_principals_for_portfolio")
        page_iterator = paginator.paginate(PortfolioId=portfolio_id)
        for page in page_iterator:
            for principal in page.get("Principals", []):
                principals.add(principal["PrincipalARN"])

        return principals
