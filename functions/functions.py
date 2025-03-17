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
