from __future__ import annotations

import httpx
import pytest
from kartoffelfax.core.fritzbox.tr064_client import (
    TR064Client,
    TR064ConnectionError,
    TR064Credentials,
    TR064Error,
)

GET_INFO_RESPONSE = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetInfoResponse xmlns:u="urn:dslforum-org:service:DeviceInfo:1">
      <NewManufacturerName>AVM</NewManufacturerName>
      <NewModelName>FRITZ!Box 7590</NewModelName>
      <NewSoftwareVersion>154.07.57</NewSoftwareVersion>
      <NewSerialNumber>3CA62F000000</NewSerialNumber>
    </u:GetInfoResponse>
  </s:Body>
</s:Envelope>"""

SOAP_FAULT = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>
<s:Fault><faultcode>s:Client</faultcode><faultstring>UPnPError</faultstring></s:Fault>
</s:Body></s:Envelope>"""

DIGEST_CHALLENGE = 'Digest realm="F!Box SOAP-Auth", nonce="abc123", algorithm=MD5, qop="auth"'


def _client(handler, **creds) -> TR064Client:
    return TR064Client(
        TR064Credentials(host="fritz.box", username="user", password="secret", **creds),
        transport=httpx.MockTransport(handler),
    )


async def test_get_device_info_sends_soap_and_parses_response() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "authorization" not in request.headers:
            return httpx.Response(401, headers={"WWW-Authenticate": DIGEST_CHALLENGE})
        seen["auth"] = request.headers["authorization"]
        seen["action"] = request.headers["soapaction"]
        seen["path"] = request.url.path
        seen["body"] = request.content.decode()
        return httpx.Response(200, text=GET_INFO_RESPONSE)

    info = await _client(handler).get_device_info()

    assert info["NewModelName"] == "FRITZ!Box 7590"
    assert info["NewSoftwareVersion"] == "154.07.57"
    assert seen["auth"].startswith("Digest ")
    assert 'username="user"' in seen["auth"]
    assert seen["action"] == "urn:dslforum-org:service:DeviceInfo:1#GetInfo"
    assert seen["path"] == "/upnp/control/deviceinfo"
    assert "<u:GetInfo" in seen["body"]


async def test_wrong_credentials_raise_tr064_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, headers={"WWW-Authenticate": DIGEST_CHALLENGE})

    with pytest.raises(TR064Error, match="Authentication"):
        await _client(handler).get_device_info()


async def test_soap_fault_raises_tr064_error() -> None:
    with pytest.raises(TR064Error, match="GetInfoResponse"):
        await _client(lambda r: httpx.Response(200, text=SOAP_FAULT)).get_device_info()


async def test_malformed_xml_raises_tr064_error() -> None:
    with pytest.raises(TR064Error, match="Malformed"):
        await _client(lambda r: httpx.Response(200, text="<not xml")).get_device_info()


async def test_unreachable_box_raises_connection_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("tunnel down", request=request)

    client = _client(handler)
    with pytest.raises(TR064ConnectionError):
        await client.get_device_info()
    assert await client.is_reachable() is False


async def test_is_reachable_true_on_200() -> None:
    assert await _client(lambda r: httpx.Response(200, text="<root/>")).is_reachable() is True
