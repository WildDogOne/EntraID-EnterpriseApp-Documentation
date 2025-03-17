import json
from kestra import Kestra
from functools import wraps
import time

logger = Kestra.logger()
# from functions.log_config import logger
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.subscription import SubscriptionClient
from msgraph.generated.models.group import Group
from functions.confluence import (
    confluence_update_page,
    style_text,
    get_childid,
    convert_to_html_table,
    get_tables,
)


def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        Kestra.timer(f"{func.__name__} Duration", end - start)
        return result

    return wrapper


def process_auth_type(apps, args=None, confluence=None, confluence_page_id=None):
    saml_apps, oauth_apps = categorize_apps(apps)
    if args.test:
        logger.info("Test Mode: Skipping Confluence Update")
    else:
        if saml_apps:
            update_confluence(
                confluence=confluence,
                confluence_page_id=confluence_page_id,
                table=saml_apps,
                title="SAML Enabled Enterprise Apps",
            )
        if oauth_apps:
            update_confluence(
                confluence=confluence,
                confluence_page_id=confluence_page_id,
                table=oauth_apps,
                title="Oauth Enabled Enterprise Apps",
            )


def process_owners(owners):
    owners_list = []
    for owner in owners:
        owners_list.append(owner.display_name)
    return owners_list


def categorize_apps(apps):
    saml_apps = []
    oauth_apps = []
    for app in apps:
        app = app.__dict__
        if "optional_claims" in app and app["optional_claims"]:
            optional_claims = app["optional_claims"].__dict__
            from pprint import pprint

            if len(app["owners"]) > 0:
                owners = ", ".join(process_owners(app["owners"]))
            else:
                owners = None
            if (
                "saml2_token" in optional_claims
                and len(optional_claims["saml2_token"]) > 0
            ):
                logger.debug(f"SAML2 Token for {app['display_name']}")
                saml_apps.append(
                    {
                        "Application": app["display_name"],
                        "AppID": app["app_id"],
                        "Owner": owners,
                    }
                )
            else:
                logger.debug(f"No SAML2 Token for {app['display_name']}")
                oauth_apps.append(
                    {
                        "Application": app["display_name"],
                        "AppID": app["app_id"],
                        "Owner": owners,
                    }
                )
    return saml_apps, oauth_apps


def update_confluence(confluence=None, confluence_page_id=None, title=None, table=None):
    confluence_update_page(
        confluence=confluence,
        title=title,
        parent_id=confluence_page_id,
        representation="storage",
        table=table,
        full_width=False,
        escape_table=True,
    )


def document_enterprise_apps(apps, args=None, confluence=None, confluence_page_id=None):
    app_table = []
    for app in apps:
        app = app.__dict__
        if "optional_claims" in app and app["optional_claims"]:
            oauthapp = True
        else:
            oauthapp = False
        if len(app["owners"]) > 0:
            owners = ", ".join(process_owners(app["owners"]))
        else:
            owners = None
        app_table.append(
            {
                "Application": app["display_name"],
                "AppID": app["app_id"],
                "Owner": owners,
                "Created": app["created_date_time"],
                "SSO": oauthapp,
            }
        )

    if args.test:
        logger.info("Test Mode: Skipping Confluence Update")
    else:
        update_confluence(
            confluence=confluence,
            confluence_page_id=confluence_page_id,
            table=app_table,
            title="Enterprise App Overview",
        )
