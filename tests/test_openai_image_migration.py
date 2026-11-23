"""Offline checks for the API shutdown migration, with the actual OpenAI SDK."""

import base64
import json
from email import policy
from email.parser import BytesParser
from io import BytesIO

import openai
import pytest
from PIL import Image

from tryon.api.openAI import image_adapter
from tryon.cli.runner import invoke_model

if int(openai.__version__.split(".", 1)[0]) >= 3:
    import httpx2 as http
else:
    import httpx as http


@pytest.fixture
def openai_wire(monkeypatch):
    requests = []
    clients = []
    buf = BytesIO()
    Image.new("RGBA", (32, 32)).save(buf, format="PNG")
    png = buf.getvalue()

    def respond(request):
        requests.append(request)
        return http.Response(
            200,
            json={
                "created": 1,
                "data": [{"b64_json": base64.b64encode(png).decode()}],
            },
        )

    def client(**kwargs):
        sdk = openai.OpenAI(
            **kwargs, http_client=http.Client(transport=http.MockTransport(respond))
        )
        clients.append(sdk)
        return sdk

    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setattr(image_adapter, "OpenAI", client)
    yield requests, png
    for sdk in clients:
        sdk.close()


def multipart_parts(request):
    header = f"Content-Type: {request.headers['Content-Type']}\r\n\r\n".encode()
    message = BytesParser(policy=policy.default).parsebytes(header + request.content)
    parts = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        parts.setdefault(name, []).append(part.get_payload(decode=True))
    return parts


def test_native_default_generation_preserves_shape_and_png_output(openai_wire):
    requests, png = openai_wire
    adapter = image_adapter.GPTImageAdapter(api_key="test-key")

    result = adapter.generate_text_to_image(
        "Generate a jacket", size="1536x1024", quality="high", background="opaque"
    )

    assert result == [png]
    assert len(requests) == 1
    request = requests[0]
    assert request.url.host == "api.openai.com"
    assert request.url.path == "/v1/images/generations"
    assert json.loads(request.content) == {
        "model": "gpt-image-2.6-flare",
        "prompt": "Generate a jacket",
        "size": "1536x1024",
        "quality": "high",
        "background": "opaque",
        "n": 1,
    }


def test_native_default_multi_image_edit_with_mask_preserves_multipart(openai_wire):
    requests, png = openai_wire
    adapter = image_adapter.GPTImageAdapter(api_key="test-key")

    result = adapter.generate_image_edit(
        images=[Image.new("RGBA", (32, 32)), Image.new("RGBA", (32, 32), "red")],
        mask=Image.new("RGBA", (32, 32)),
        prompt="Change the jacket",
        size="1024x1536",
        quality="medium",
        background="transparent",
    )

    assert result == [png]
    assert len(requests) == 1
    request = requests[0]
    assert request.url.path == "/v1/images/edits"
    fields = multipart_parts(request)
    assert fields["model"] == [b"gpt-image-2.6-flare"]
    assert fields["size"] == [b"1024x1536"]
    assert fields["quality"] == [b"medium"]
    assert fields["background"] == [b"transparent"]
    assert fields["n"] == [b"1"]
    assert "input_fidelity" not in fields
    images = fields.get("image[]", fields.get("image", []))
    assert len(images) == 2
    assert Image.open(BytesIO(images[1])).getpixel((0, 0)) == (255, 0, 0, 255)
    assert fields["mask"] == [png]


def test_explicit_legacy_model_keeps_fidelity_on_openai(openai_wire):
    requests, _ = openai_wire
    adapter = image_adapter.GPTImageAdapter(
        api_key="test-key", model_version="gpt-image-1.5"
    )

    adapter.generate_image_edit(
        Image.new("RGB", (32, 32)), "Edit", input_fidelity="high"
    )

    fields = multipart_parts(requests[0])
    assert fields["model"] == [b"gpt-image-1.5"]
    assert fields["input_fidelity"] == [b"high"]


def test_compatible_gateway_keeps_default_and_fidelity(monkeypatch, openai_wire):
    requests, _ = openai_wire
    monkeypatch.setenv("OPENAI_BASE_URL", "https://gateway.example/v1")
    adapter = image_adapter.GPTImageAdapter(api_key="test-key")

    adapter.generate_image_edit(Image.new("RGB", (32, 32)), "Edit")

    assert requests[0].url.host == "gateway.example"
    fields = multipart_parts(requests[0])
    assert fields["model"] == [b"gpt-image-1.5"]
    assert fields["input_fidelity"] == [b"low"]


def test_native_sunburst_rejects_explicit_legacy_fidelity(openai_wire):
    requests, _ = openai_wire
    adapter = image_adapter.GPTImageAdapter(
        api_key="test-key", model_version="gpt-image-2.6-sunburst"
    )

    with pytest.raises(ValueError, match="Omit input_fidelity"):
        adapter.generate_image_edit(
            Image.new("RGB", (32, 32)), "Edit", input_fidelity="low"
        )
    assert not requests


def test_generic_routes_do_not_force_a_model_or_fidelity(openai_wire, monkeypatch, tmp_path):
    requests, _ = openai_wire
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    image = tmp_path / "input.png"
    Image.new("RGBA", (32, 32)).save(image)

    generated = invoke_model("generate", "gpt-image", output_dir=str(tmp_path), prompt="make a dress")
    edited = invoke_model("edit", "gpt-image", output_dir=str(tmp_path), images=[str(image)], prompt="make it red")

    assert generated["success"], generated
    assert edited["success"], edited
    assert json.loads(requests[0].content)["model"] == "gpt-image-2.6-flare"
    fields = multipart_parts(requests[1])
    assert fields["model"] == [b"gpt-image-2.6-flare"]
    assert "input_fidelity" not in fields
