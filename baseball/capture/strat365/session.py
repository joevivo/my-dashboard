"""
BIE Component:
Capture Infrastructure

Purpose:
Provide a reusable HTTP session for Strat365 capture.

Responsibilities
----------------
- Build absolute URLs
- Manage cookies
- Provide GET and POST operations
- Set a consistent User-Agent
- Support retries (future)
- Support authentication (future)

This module contains NO baseball logic.

Version:
0.1
"""

from urllib.parse import urljoin
import requests


class Strat365Session:

    def __init__(self, base_url="https://365.strat-o-matic.com"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Baseball Intelligence Engine/0.1",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def url(self, path):
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def get(self, path, **kwargs):
        response = self.session.get(self.url(path), timeout=30, **kwargs)
        response.raise_for_status()
        return response.text

    def post(self, path, data=None, **kwargs):
        response = self.session.post(
            self.url(path),
            data=data,
            timeout=30,
            **kwargs
        )
        response.raise_for_status()
        return response.text
