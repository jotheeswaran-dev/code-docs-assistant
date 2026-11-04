"""Module doc."""

import os
from pathlib import Path

TIMEOUT = 30


class Session:
    """An HTTP session."""

    retries = 3

    def send(self, request):
        """Send one request."""
        return request

    async def close(self):
        return None


def build(timeout=TIMEOUT):
    return Session()
