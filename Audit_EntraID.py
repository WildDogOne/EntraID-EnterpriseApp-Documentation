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
from functions.functions import timer_decorator
from functions.confluence import confluence_update_page
from atlassian import Confluence
from functions.msgraphapi import GraphAPI

logger = Kestra.logger()


@timer_decorator
async def process_saml(apps, args=None, confluence=None):
    saml_apps = []
    oauth_apps = []
    for app in apps:
        app = app.__dict__
        # if app.app_id == "d489c7c6-9c9a-4045-9207-8e286a987a1e":
        if "optional_claims" in app and app["optional_claims"]:
            optional_claims = app["optional_claims"].__dict__
            if "saml2_token" in optional_claims:
                if len(optional_claims["saml2_token"]) > 0:
                    saml_apps.append(
                        {"Application": app["display_name"], "AppID": app["app_id"]}
                    )
            else:
                logger.debug(f"No SAML2 Token for {app['display_name']}")
                oauth_apps.append(
                    {"Application": app["display_name"], "AppID": app["app_id"]}
                )
    if args.test:
        logger.info("Test Mode: Skipping Confluence Update")
    else:
        if len(saml_apps) > 0:
            confluence_update_page(
                confluence=confluence,
                title="SAML Enabled Enterprise Apps",
                parent_id=confluence_page_id,
                representation="storage",
                table=saml_apps,
                full_width=False,
                escape_table=True,
            )
        if len(oauth_apps) > 0:
            confluence_update_page(
                confluence=confluence,
                title="Oauth Enabled Enterprise Apps",
                parent_id=confluence_page_id,
                representation="storage",
                table=oauth_apps,
                full_width=False,
                escape_table=True,
            )


@timer_decorator
async def audit_entraid(graph_client=None, confluence=None, args=None):
    enterpriseapps = await graph_client.get_all_enterprise_apps()
    await process_saml(enterpriseapps, args=args, confluence=confluence)

    if args.test:
        logger.info("Test Mode: Skipping Confluence Update")
    else:
        confluence_update_page(
            confluence=confluence,
            title="EntraID App",
            parent_id=confluence_page_id,
            representation="storage",
            full_width=False,
            escape_table=True,
        )


@timer_decorator
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
