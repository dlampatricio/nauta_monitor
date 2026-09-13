from __future__ import annotations

from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from nauta_monitor.parser import AccountInfo, find_error, parse_account_info

BASE_URL = "https://secure.etecsa.net:8443"
QUERY_SERVLET = f"{BASE_URL}/EtecsaQueryServlet"

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-419,es;q=0.6",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
}


class PortalError(Exception):
    pass


class PortalInitError(PortalError):
    pass


class QueryError(PortalError):
    pass


@dataclass
class PortalSession:
    csrf_hw: str
    wlan_user_ip: str


class SecurePortalClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20.0):
        self._base_url = (base_url or BASE_URL).rstrip("/")
        self._query_servlet = f"{self._base_url}/EtecsaQueryServlet"
        self._session = requests.Session()
        self._session.headers.update(_HEADERS)
        self._timeout = timeout

    def init_session(self) -> PortalSession:
        try:
            response = self._session.get(self._base_url, timeout=self._timeout)
        except requests.RequestException as exc:
            raise PortalInitError(f"No se pudo acceder a {self._base_url}: {exc}") from exc
        form = self._extract_form(response.text)
        if form is None:
            raise PortalInitError(
                "No se encontró el formulario de acceso en el portal (¿estás conectado a la red ETECSA?). "
                "Inténtalo con --verbose para inspeccionar la respuesta."
            )
        csrf_hw = form.get("CSRFHW")
        wlan_user_ip = form.get("wlanuserip")
        if not csrf_hw or not wlan_user_ip:
            raise PortalInitError("El formulario del portal no incluye CSRFHW/wlanuserip.")
        return PortalSession(csrf_hw=csrf_hw, wlan_user_ip=wlan_user_ip)

    def query_account(self, username: str, password: str, portal: PortalSession) -> AccountInfo:
        return parse_account_info(self.query_account_raw(username, password, portal))

    def query_account_raw(self, username: str, password: str, portal: PortalSession) -> str:
        data = {
            "username": username,
            "password": password,
            "wlanuserip": portal.wlan_user_ip,
            "CSRFHW": portal.csrf_hw,
            "lang": "",
        }
        try:
            response = self._session.post(self._query_servlet, data=data, timeout=self._timeout)
        except requests.RequestException as exc:
            raise QueryError(f"Fallo al consultar {self._query_servlet}: {exc}") from exc
        error = find_error(response.text)
        if error:
            raise QueryError(f"El portal respondió con un error: {error}")
        return response.text

    @staticmethod
    def _extract_form(html: str) -> dict | None:
        soup = BeautifulSoup(html, "html5lib")
        form = soup.select_one("form#formulario") or soup.select_one("form[id]")
        if form is None:
            return None
        return {
            inp.get("name"): inp.get("value", "")
            for inp in form.select("input[name]")
            if inp.get("name")
        }