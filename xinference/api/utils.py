# Copyright 2022-2023 XProbe Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging

import fastapi
import gradio_client.utils as client_utils
import httpx

logger = logging.getLogger(__name__)


def get_root_url(
    request: fastapi.Request, route_path: str, root_path: str | None
) -> str:
    """
    Gets the root url of the Gradio app (i.e. the public url of the app) without a trailing slash.

    This is how the root_url is resolved:
    1. If a user provides a `root_path` manually that is a full URL, it is returned directly.
    2. If the request has an x-forwarded-host header (e.g. because it is behind a proxy), the root url is
    constructed from the x-forwarded-host header. In this case, `route_path` is not used to construct the root url.
    3. Otherwise, the root url is constructed from the request url. The query parameters and `route_path` are stripped off.
    And if a relative `root_path` is provided, and it is not already the subpath of the URL, it is appended to the root url.

    In cases (2) and (3), We also check to see if the x-forwarded-proto header is present, and if so, convert the root url to https.
    And if there are multiple hosts in the x-forwarded-host or multiple protocols in the x-forwarded-proto, the first one is used.
    """

    def get_first_header_value(header_name: str):
        header_value = request.headers.get(header_name)
        if header_value:
            return header_value.split(",")[0].strip()
        return None

    if root_path and client_utils.is_http_url_like(root_path):
        return root_path.rstrip("/")

    x_forwarded_host = get_first_header_value("x-forwarded-host")
    logger.info("successful hack gradio")
    root_url = str(request.url)
    root_url = httpx.URL(root_url)
    root_url = root_url.copy_with(query=None)  # type: ignore
    root_url = str(root_url).rstrip("/")
    if get_first_header_value("x-forwarded-proto") == "https":
        root_url = root_url.replace("http://", "https://")

    route_path = route_path.rstrip("/")
    if len(route_path) > 0 and not x_forwarded_host:
        root_url = root_url[: -len(route_path)]
    root_url = root_url.rstrip("/")

    root_url = httpx.URL(root_url)
    if root_path and root_url.path != root_path:  # type: ignore
        root_url = root_url.copy_with(path=root_path)  # type: ignore

    return str(root_url).rstrip("/")
