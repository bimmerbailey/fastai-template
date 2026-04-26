import io

import pytest

from fastai.storage.core import StorageService, StorageSettings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_upload_and_download_bytes(storage: StorageService) -> None:
    key = "test/hello.txt"
    data = b"hello world"

    await storage.upload_bytes(data, key, content_type="text/plain")

    result = await storage.download_bytes(key)
    assert result == data


@pytest.mark.asyncio
async def test_upload_and_download_fileobj(storage: StorageService) -> None:
    key = "test/fileobj.bin"
    content = b"binary content here"
    upload_buf = io.BytesIO(content)

    await storage.upload_fileobj(upload_buf, key)

    download_buf = io.BytesIO()
    await storage.download_fileobj(key, download_buf)
    download_buf.seek(0)
    assert download_buf.read() == content


@pytest.mark.asyncio
async def test_object_exists(storage: StorageService) -> None:
    key = "test/exists-check.txt"

    assert await storage.object_exists(key) is False

    await storage.upload_bytes(b"data", key)

    assert await storage.object_exists(key) is True


@pytest.mark.asyncio
async def test_delete_object(storage: StorageService) -> None:
    key = "test/to-delete.txt"
    await storage.upload_bytes(b"delete me", key)
    assert await storage.object_exists(key) is True

    await storage.delete_object(key)

    assert await storage.object_exists(key) is False


@pytest.mark.asyncio
async def test_list_objects(storage: StorageService) -> None:
    keys = ["docs/a.txt", "docs/b.txt", "other/c.txt"]
    for key in keys:
        await storage.upload_bytes(b"x", key)

    all_objects = await storage.list_objects()
    assert len(all_objects) == 3

    docs_only = await storage.list_objects(prefix="docs/")
    assert len(docs_only) == 2
    returned_keys = {obj.key for obj in docs_only}
    assert returned_keys == {"docs/a.txt", "docs/b.txt"}


@pytest.mark.asyncio
async def test_list_objects_max_keys(storage: StorageService) -> None:
    for i in range(5):
        await storage.upload_bytes(b"x", f"item/{i}.txt")

    limited = await storage.list_objects(prefix="item/", max_keys=3)
    assert len(limited) <= 3


@pytest.mark.asyncio
async def test_generate_presigned_url(
    storage: StorageService,
    storage_settings: StorageSettings,
) -> None:
    key = "test/presigned.txt"
    await storage.upload_bytes(b"signed content", key)

    url = await storage.generate_presigned_url(key)
    assert isinstance(url, str)
    assert storage_settings.bucket in url
    assert "presigned" in url


@pytest.mark.asyncio
async def test_upload_bytes_content_type(storage: StorageService) -> None:
    key = "test/typed.json"
    await storage.upload_bytes(b'{"a": 1}', key, content_type="application/json")

    bucket = storage.bucket
    obj = await bucket.Object(key)
    await obj.load()
    content_type = await obj.content_type
    assert content_type == "application/json"
