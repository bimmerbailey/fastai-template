from typing import IO, Self

import aioboto3
import structlog.stdlib
from aioboto3.session import ResourceCreatorContext
from botocore.exceptions import ClientError
from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict
from types_aiobotocore_s3 import S3ServiceResource
from types_aiobotocore_s3.service_resource import Bucket, ObjectSummary

from fastai.utils.settings import FastAISettings

logger = structlog.stdlib.get_logger(__name__)


class StorageSettings(FastAISettings):
    """S3-compatible object storage settings.

    Configure via environment variables prefixed with ``FASTAI_STORAGE_``.
    Defaults match the local MinIO service in ``compose.yml``.
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_STORAGE_")

    # NOTE no "endpoint_url" when running in aws
    endpoint_url: str | None = None
    access_key: SecretStr
    secret_key: SecretStr
    region: str = "us-east-1"
    bucket: str = "fastai"

    def create_session(self) -> aioboto3.Session:
        """Create an aioboto3 session from these settings.

        The session is lightweight and safe to share across coroutines.
        Store it on app state and reuse for the lifetime of the process.
        """
        return aioboto3.Session(
            aws_access_key_id=self.access_key.get_secret_value(),
            aws_secret_access_key=self.secret_key.get_secret_value(),
            region_name=self.region,
        )

    def create_resource(self) -> ResourceCreatorContext:
        """Create an S3 resource context manager.

        Per project convention, Settings classes provide a method to create
        the underlying client. The caller manages the lifecycle::

            async with settings.create_resource() as resource:
                ...
        """
        session = self.create_session()
        return session.resource("s3", endpoint_url=self.endpoint_url)


class StorageService:
    """Async S3-compatible object storage service.

    Must be used as an async context manager::

        async with StorageService(settings) as svc:
            await svc.upload_bytes(b"data", "key")
    """

    def __init__(self, settings: StorageSettings) -> None:
        self._settings = settings
        self._resource: S3ServiceResource | None = None
        self._bucket: Bucket | None = None

    async def __aenter__(self) -> Self:
        self._resource_cm = self._settings.create_resource()
        self._resource = await self._resource_cm.__aenter__()  # type: ignore[union-attr]
        self._bucket = await self._resource.Bucket(self._settings.bucket)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._resource_cm.__aexit__(*exc_info)  # type: ignore[union-attr]
        self._resource = None
        self._bucket = None

    @property
    def resource(self) -> S3ServiceResource:
        if self._resource is None:
            raise RuntimeError(
                "StorageService must be used as an async context manager."
            )
        return self._resource

    @property
    def bucket(self) -> Bucket:
        if self._bucket is None:
            raise RuntimeError(
                "StorageService must be used as an async context manager."
            )
        return self._bucket

    async def upload_fileobj(
        self,
        fileobj: IO[bytes],
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file-like object to S3.

        Returns the ETag of the uploaded object (quotes stripped).
        """
        b = self.bucket
        await b.upload_fileobj(
            Fileobj=fileobj,
            Key=key,
            ExtraArgs={"ContentType": content_type},
        )
        obj = await b.Object(key)
        await obj.load()
        etag: str = (await obj.e_tag).strip('"')
        logger.info("Uploaded object", bucket=b.name, key=key, etag=etag)
        return etag

    async def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to S3.

        Returns the ETag of the uploaded object (quotes stripped).
        """
        b = self.bucket
        obj = await b.put_object(Key=key, Body=data, ContentType=content_type)
        etag: str = (await obj.e_tag).strip('"')
        logger.info("Uploaded object", bucket=b.name, key=obj.key, etag=etag)
        return etag

    async def download_fileobj(
        self,
        key: str,
        fileobj: IO[bytes],
    ) -> None:
        """Download an S3 object into a file-like object."""
        b = self.bucket
        await b.download_fileobj(Key=key, Fileobj=fileobj)
        logger.info("Downloaded object", bucket=b.name, key=key)

    async def download_bytes(
        self,
        key: str,
    ) -> bytes:
        """Download an S3 object and return its contents as bytes."""
        b = self.bucket
        obj = await b.Object(key)
        response = await obj.get()
        data = await response["Body"].read()
        logger.info("Downloaded object", bucket=b.name, key=key)
        return data

    async def delete_object(
        self,
        key: str,
    ) -> None:
        """Delete a single object from S3."""
        b = self.bucket
        obj = await b.Object(key)
        await obj.delete()
        logger.info("Deleted object", bucket=b.name, key=key)

    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[ObjectSummary]:
        """List objects in a bucket, optionally filtered by prefix."""
        b = self.bucket
        collection = b.objects.filter(Prefix=prefix).limit(max_keys)
        return [obj async for obj in collection]

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate a presigned URL for temporary access to an object."""
        b = self.bucket
        client_method = "get_object" if http_method == "GET" else "put_object"
        url: str = await b.meta.client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": b.name, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    async def object_exists(
        self,
        key: str,
    ) -> bool:
        """Check whether an object exists in the bucket."""
        b = self.bucket
        try:
            obj = await b.Object(key)
            await obj.load()
            return True
        except ClientError:
            return False
