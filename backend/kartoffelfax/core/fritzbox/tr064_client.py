"""TR-064 SOAP client for Fritz!Box: device info, call monitoring, WAN/VPN status.

Works over a plain LAN connection or a WireGuard tunnel transparently, since it
only needs an IP/port reachable from this host (VPN-side Fritz!Box IP, e.g.
192.168.178.1 over wg0, or the LAN IP directly).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

_DEVICEINFO_SERVICE = "urn:dslforum-org:service:DeviceInfo:1"
_DEVICEINFO_CONTROL_URL = "/upnp/control/deviceinfo"

_SOAP_ENVELOPE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
    's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    "<s:Body><u:{action} xmlns:u=\"{service}\"/></s:Body>"
    "</s:Envelope>"
)


@dataclass(slots=True)
class TR064Credentials:
    host: str
    port: int = 49000
    username: str | None = None
    password: str | None = None


class TR064ConnectionError(RuntimeError):
    """Raised when the Fritz!Box is unreachable (e.g. VPN tunnel down)."""


class TR064Error(RuntimeError):
    """Raised when the Fritz!Box answers but rejects the request (auth failure, SOAP fault)."""


class TR064Client:
    """Minimal async TR-064 client, built on top of httpx + SOAP envelopes."""

    def __init__(
        self,
        credentials: TR064Credentials,
        timeout: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._creds = credentials
        self._timeout = timeout
        self._transport = transport

    @property
    def base_url(self) -> str:
        return f"http://{self._creds.host}:{self._creds.port}"

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self._timeout, transport=self._transport)

    async def is_reachable(self) -> bool:
        """Quick reachability probe, used by /api/settings/connections/{id}/test."""
        try:
            async with self._http() as client:
                resp = await client.get(f"{self.base_url}/tr64desc.xml")
                return resp.status_code == 200
        except (TimeoutError, httpx.TransportError):
            return False

    async def get_device_info(self) -> dict[str, str]:
        """Calls GetInfo on urn:dslforum-org:service:DeviceInfo:1."""
        auth = None
        if self._creds.username and self._creds.password:
            auth = httpx.DigestAuth(self._creds.username, self._creds.password)

        try:
            async with self._http() as client:
                resp = await client.post(
                    f"{self.base_url}{_DEVICEINFO_CONTROL_URL}",
                    content=_SOAP_ENVELOPE.format(action="GetInfo", service=_DEVICEINFO_SERVICE),
                    headers={
                        "Content-Type": 'text/xml; charset="utf-8"',
                        "SOAPAction": f"{_DEVICEINFO_SERVICE}#GetInfo",
                    },
                    auth=auth,
                )
        except (TimeoutError, httpx.TransportError) as exc:
            raise TR064ConnectionError(f"Fritz!Box at {self.base_url} is unreachable: {exc}") from exc

        if resp.status_code == 401:
            raise TR064Error("Authentication failed (check TR-064 username/password)")
        if resp.status_code != 200:
            raise TR064Error(f"Unexpected HTTP status {resp.status_code} from Fritz!Box")
        return _parse_get_info(resp.text)


def _parse_get_info(xml_text: str) -> dict[str, str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TR064Error(f"Malformed SOAP response: {exc}") from exc

    for element in root.iter():
        if element.tag.endswith("}GetInfoResponse") or element.tag == "GetInfoResponse":
            return {child.tag.rsplit("}", 1)[-1]: (child.text or "") for child in element}
    raise TR064Error("SOAP response contains no GetInfoResponse (fault?)")
