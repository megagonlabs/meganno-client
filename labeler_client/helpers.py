import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from labeler_client.constants import NO_TIMEOUT_ENDPOINTS, REQUEST_TIMEOUT_SECONDS


def requests_retry_session(
    retries=0,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def delete_request(path="", json={}, timeout=REQUEST_TIMEOUT_SECONDS):
    for endpoint in NO_TIMEOUT_ENDPOINTS.get("get", []):
        if path.endswith(endpoint):
            timeout = None
            break
    try:
        return requests_retry_session().delete(path, json=json, timeout=timeout)
    except requests.ConnectTimeout as ex:
        raise Exception("{}: {}".format(ex.__class__.__name__, "408 Request Timeout"))


def put_request(path="", json={}, timeout=REQUEST_TIMEOUT_SECONDS):
    for endpoint in NO_TIMEOUT_ENDPOINTS.get("post", []):
        if path.endswith(endpoint):
            timeout = None
            break
    try:
        return requests_retry_session().put(path, json=json, timeout=timeout)
    except requests.ConnectTimeout as ex:
        raise Exception("{}: {}".format(ex.__class__.__name__, "408 Request Timeout"))


def get_request(path="", json={}, timeout=REQUEST_TIMEOUT_SECONDS):
    for endpoint in NO_TIMEOUT_ENDPOINTS.get("get", []):
        if path.endswith(endpoint):
            timeout = None
            break
    try:
        return requests_retry_session().get(path, json=json, timeout=timeout)
    except requests.ConnectTimeout as ex:
        raise Exception("{}: {}".format(ex.__class__.__name__, "408 Request Timeout"))


def post_request(path="", json={}, timeout=REQUEST_TIMEOUT_SECONDS):
    for endpoint in NO_TIMEOUT_ENDPOINTS.get("post", []):
        if path.endswith(endpoint):
            timeout = None
            break
    try:
        return requests_retry_session().post(path, json=json, timeout=timeout)
    except requests.ConnectTimeout as ex:
        raise Exception("{}: {}".format(ex.__class__.__name__, "408 Request Timeout"))


def put_request(path="", json={}, timeout=REQUEST_TIMEOUT_SECONDS):
    for endpoint in NO_TIMEOUT_ENDPOINTS.get("put", []):
        if path.endswith(endpoint):
            timeout = None
            break
    try:
        return requests_retry_session().put(path, json=json, timeout=timeout)
    except requests.ConnectTimeout as ex:
        raise Exception("{}: {}".format(ex.__class__.__name__, "408 Request Timeout"))
