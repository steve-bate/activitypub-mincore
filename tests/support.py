import json
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi.testclient import TestClient


@dataclass
class MockRequest:
    method: str
    url: str
    options: dict


@dataclass
class MockResponse:
    content: bytes
    method: str = field(default="get")
    status_code: int = field(default=200)


class MockServer:
    def __init__(self, test_client: TestClient, monkeypatch):
        self.requests: list[MockRequest] = []
        self._get_responses: dict[str, MockResponse] = {}
        self._post_responses: dict[str, MockResponse] = {}
        self._test_client = test_client
        self._test_client_complete = False
        monkeypatch.setattr(httpx.AsyncClient, "__aenter__", self)

    def _ensure_client_completion(self):
        if not self._test_client_complete:
            self._test_client.__exit__()
            self._test_client_complete = True

    def add_response(
        self,
        url: str,
        data: str | bytes | dict,
        method: str = "get",
        status_code: int = 200,
    ):
        if isinstance(data, str):
            data = data.encode()
        elif isinstance(data, dict):
            data = json.dumps(data).encode()
        response = MockResponse(
            method=method.lower(),
            content=data,
            status_code=status_code,
        )
        responses = self._get_responses if method == "get" else self._post_responses
        responses[url] = response

    @staticmethod
    def _httpx_error_response(
        method: str, url: str, status_code: int
    ) -> httpx.Response:
        httpx_response = httpx.Response(
            404, stream=httpx._transports.default.ResponseStream([])
        )
        httpx_response.request = httpx.Request(method, url)
        return httpx_response

    def sync_get(self, args, kwargs):
        self.requests.append(MockRequest(method="get", url=args[0], options=kwargs))
        mock_response = self._get_responses.get(args[0])
        if mock_response:
            # # May support a "count" in the future
            # del self._get_responses[args[0]]
            return self._to_httpx_response(args[0], mock_response)
        else:
            return self._httpx_error_response("get", args[0], 404)

    async def get(self, *args, **kwargs):
        return self.sync_get(args, kwargs)

    @staticmethod
    def _to_httpx_response(url: str, mock_response: MockResponse):
        payload = mock_response.content
        httpx_response = httpx.Response(
            mock_response.status_code,
            stream=httpx._transports.default.ResponseStream([payload]),
        )
        httpx_response.request = httpx.Request(mock_response.method, url)
        setattr(httpx_response, "_content", payload)
        return httpx_response

    def sync_post(self, args, kwargs):
        url = args[0]
        self.requests.append(
            MockRequest(
                method="post",
                url=url,
                options=kwargs,
            )
        )
        mock_response = self._post_responses.get(url)
        if mock_response:
            return self._to_response(url, mock_response)
        else:
            response = httpx.Response(status_code=200)
            response.request = httpx.Request("post", url)
            return response

    async def post(self, *args, **kwargs):
        return self.sync_post(args, kwargs)

    def received_post(self, pattern: dict[str, Any]) -> MockRequest | None:
        for request in self.requests:
            if request.method == "post":
                if "json" in request.options:
                    payload = request.options["json"]
                    matched = True
                    for k, v in pattern.items():
                        if k not in payload or payload[k] != v:
                            matched = False
                            break
                    if matched:
                        return request
        return None

    # __aenter callback
    async def __call__(self, *args):
        return self
