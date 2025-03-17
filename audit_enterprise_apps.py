import asyncio
from kestra import Kestra
import argparse


from creds import (
    azure_tenant_id,
    azure_client_id,
    azure_client_secret,
    confluence_page_id,
    confluence_token,
    confluence_url,
)
from functions.functions import (
    timer_decorator,
    process_auth_type,
    document_enterprise_apps,
)
from functions.confluence import confluence_update_page
from atlassian import Confluence
from functions.msgraphapi import GraphAPI

logger = Kestra.logger()


@timer_decorator
async def get_entraid_enterprise_apps(graph_client=None):
    enterpriseapps = await graph_client.get_all_enterprise_apps()
    return enterpriseapps


@timer_decorator
async def audit_entraid(graph_client=None, confluence=None, args=None):
    # enterpriseapps = await graph_client.get_all_enterprise_apps()
    enterpriseapps = await get_entraid_enterprise_apps(graph_client=graph_client)
    process_auth_type(
        enterpriseapps,
        args=args,
        confluence=confluence,
        confluence_page_id=confluence_page_id,
    )

    document_enterprise_apps(
        enterpriseapps,
        args=args,
        confluence=confluence,
        confluence_page_id=confluence_page_id,
    )


async def main():
    parser = argparse.ArgumentParser(
        prog="PIM EntraID Role Sync",
        description="Sync EntraID Role Assignments from Azure PIM to Confluence",
    )
    parser.add_argument(
        "-t",
        "--test",
        help="Dryrun the script without writing to Confluence",
        action="store_true",
    )
    args = parser.parse_args()
    if args.test:
        logger.info("Running in Test Mode")

    graph_client = GraphAPI(
        azure_tenant_id=azure_tenant_id,
        azure_client_id=azure_client_id,
        azure_client_secret=azure_client_secret,
    )
    confluence = Confluence(url=confluence_url, token=confluence_token)
    await audit_entraid(graph_client=graph_client, confluence=confluence, args=args)


if __name__ == "__main__":
    asyncio.run(main())
