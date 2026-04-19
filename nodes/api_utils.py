from __future__ import annotations

import base64
import io
import os
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"


def require_package(module_name: str, install_hint: str, attr_name: str | None = None):
    try:
        module = __import__(module_name, fromlist=[attr_name] if attr_name else [])
    except ImportError as exc:
        message = (
            f"Missing dependency '{module_name}'. "
            f"Install it with `{install_hint}` inside your ComfyUI Python environment."
        )
        raise RuntimeError(message) from exc

    if attr_name is None:
        return module
    return getattr(module, attr_name)


def ensure_text(value: str, field_name: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise ValueError(f"{field_name} cannot be empty.")
    return clean_value


def format_api_exception(provider_name: str, exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    lowered = message.lower()
    if "connection error" in lowered or "timed out" in lowered or "timeout" in lowered:
        message = (
            f"{message} "
            f"Please verify this machine can reach {DEFAULT_ARK_BASE_URL} and then retry."
        )
    return f"{provider_name} request failed: {message}"


def create_ark_client(api_key: str, base_url: str = DEFAULT_ARK_BASE_URL):
    ark_cls = require_package(
        "volcenginesdkarkruntime",
        'pip install "volcengine-python-sdk[ark]>=4.0.6"',
        "Ark",
    )
    return ark_cls(api_key=ensure_text(api_key, "api_key"), base_url=base_url)


def post_ark_json(
    api_key: str,
    endpoint_path: str,
    payload: dict,
    timeout: int = 300,
    base_url: str = DEFAULT_ARK_BASE_URL,
):
    requests = require_package("requests", "pip install requests>=2.31.0")
    url = f"{base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ensure_text(api_key, 'api_key')}",
    }

    session = requests.Session()
    session.trust_env = False
    response = session.post(url, headers=headers, json=payload, timeout=timeout)
    if response.ok:
        return response.json()

    try:
        error_body = response.json()
    except Exception:
        response.raise_for_status()
        raise RuntimeError("Unexpected error while calling Ark API.")

    raise requests.HTTPError(f"Error code: {response.status_code} - {error_body}", response=response)


def configure_dashscope(api_key: str, base_url: str = DEFAULT_DASHSCOPE_BASE_URL):
    dashscope = require_package("dashscope", "pip install dashscope>=1.22.0")
    dashscope.api_key = ensure_text(api_key, "api_key")
    dashscope.base_http_api_url = base_url
    return dashscope


def extract_first_image_url(response: Any) -> str | None:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    if not data:
        return None

    first_item = data[0]
    if isinstance(first_item, dict):
        return first_item.get("url")
    return getattr(first_item, "url", None)


def extract_text_response_content(response: Any) -> str:
    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")
    if output is None:
        raise RuntimeError("The model response did not include an output payload.")

    choices = getattr(output, "choices", None)
    if choices is None and isinstance(output, dict):
        choices = output.get("choices")
    if not choices:
        raise RuntimeError("The model response did not include any choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")
    if message is None:
        raise RuntimeError("The model response did not include a message payload.")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if content is None:
        raise RuntimeError("The model response did not include any content.")

    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue

        if isinstance(item, dict):
            if "text" in item and item["text"]:
                parts.append(str(item["text"]))
                continue
            if item.get("type") == "text" and item.get("text"):
                parts.append(str(item["text"]))
                continue

        text_value = getattr(item, "text", None)
        if text_value:
            parts.append(str(text_value))

    joined = "\n".join(part.strip() for part in parts if part and str(part).strip())
    if not joined:
        raise RuntimeError("The model response content was empty.")
    return joined


def is_probably_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://") or value.startswith("data:")


def normalize_media_reference(value: str, field_name: str) -> str:
    clean_value = ensure_text(value, field_name)
    if is_probably_url(clean_value):
        return clean_value

    path = Path(clean_value).expanduser()
    if not path.is_file():
        raise ValueError(f"{field_name} must be a valid URL, data URI, or existing file path.")
    return str(path.resolve())


def download_image_as_tensor(image_url: str):
    requests = require_package("requests", "pip install requests>=2.31.0")
    response = requests.get(image_url, timeout=120)
    response.raise_for_status()
    return image_bytes_to_tensor(response.content)


def image_bytes_to_tensor(image_bytes: bytes):
    image_module = require_package("PIL", "pip install Pillow>=10.0.0", "Image")
    with image_module.open(io.BytesIO(image_bytes)) as pil_image:
        return pil_image_to_tensor(pil_image)


def pil_image_to_tensor(pil_image):
    numpy = require_package("numpy", "pip install numpy>=1.26.0")
    torch = require_package("torch", "use the ComfyUI Python environment that already ships with torch")

    rgb_image = pil_image.convert("RGB")
    image_array = numpy.asarray(rgb_image).astype("float32") / 255.0
    return torch.from_numpy(image_array)[None, ...]


def comfy_image_to_temp_file(image_tensor, suffix: str = ".png") -> str:
    image_module = require_package("PIL", "pip install Pillow>=10.0.0", "Image")
    numpy = require_package("numpy", "pip install numpy>=1.26.0")

    image_batch = image_tensor[0].detach().cpu().numpy()
    clipped = numpy.clip(image_batch * 255.0, 0, 255).astype("uint8")
    pil_image = image_module.fromarray(clipped)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        pil_image.save(temp_file.name)
        return temp_file.name


def comfy_image_to_data_uris(image_tensor, image_format: str = "PNG") -> list[str]:
    image_module = require_package("PIL", "pip install Pillow>=10.0.0", "Image")
    numpy = require_package("numpy", "pip install numpy>=1.26.0")

    normalized_format = image_format.upper()
    mime_format = "jpeg" if normalized_format == "JPG" else normalized_format.lower()
    batch = image_tensor.detach().cpu().numpy()
    data_uris: list[str] = []

    for image_batch in batch:
        clipped = numpy.clip(image_batch * 255.0, 0, 255).astype("uint8")
        pil_image = image_module.fromarray(clipped)
        buffer = io.BytesIO()
        pil_image.save(buffer, format=normalized_format)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data_uris.append(f"data:image/{mime_format};base64,{encoded}")

    return data_uris


def safe_remove_file(file_path: str | None):
    if not file_path:
        return
    try:
        os.remove(file_path)
    except OSError:
        pass
