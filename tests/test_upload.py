import os

from fastapi.testclient import TestClient

from ai_spider.s3 import get_s3
from ai_spider.util import USER_BUCKET_NAME
from tests.util import s3_server  # noqa
from util import set_bypass_token

set_bypass_token()

from ai_spider.app import app

client = TestClient(app)


async def test_upl(s3_server):
    s3 = await get_s3()
    lora_key = "hello.world"
    upload_id = (await s3.create_multipart_upload(Bucket=USER_BUCKET_NAME, Key=lora_key))['UploadId']
    assert upload_id


async def test_file_operations(s3_server):
    # Upload a file
    token = os.environ["BYPASS_TOKEN"]
    headers = {"authorization": "bearer: " + token}

    response = client.post("/v1/files", files={"file": ("test_file.txt", "some content")},
                           data={"purpose": "fine-tune"}, headers=headers)
    assert response.status_code == 200
    file_id = response.json()["id"]

    # List files and check if the uploaded file is listed
    response = client.get("/v1/files", headers=headers)
    assert response.status_code == 200
    assert any(f["id"] == file_id for f in response.json()["data"])

    # Get the content of the uploaded file
    response = client.get(f"/v1/files/{file_id}/content", headers=headers)
    assert response.status_code == 200
    assert response.content == b"some content"

    # Delete the uploaded file
    response = client.delete(f"/v1/files/{file_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Check if the file is deleted by trying to fetch its content
    response = client.get(f"/v1/files/{file_id}/content", headers=headers)
    assert response.status_code == 404
