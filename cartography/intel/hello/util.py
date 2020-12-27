import logging

import requests.auth

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def fetch_greetings_gist():
    uri = "https://gist.githubusercontent.com/sampowers/128284db15091d4bab728f60f469d1d0/raw/2c6905d8e122c2a02765aaea3429014453ca8e64/greetings.json"

    try:
        response = requests.get(
            uri,
            headers={'Accept': 'application/json'},
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning(f"Hello: requests.get('{uri}') timed out.")
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()
