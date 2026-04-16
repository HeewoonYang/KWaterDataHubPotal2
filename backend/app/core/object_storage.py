"""
오브젝트 스토리지 추상화 (MinIO / S3 호환)

K8s 프로덕션 환경에서 backend Pod 는 언제든 스케일/재시작 되므로
파일을 로컬 디스크(/app/uploads 등)에 쓰면 다른 파드에서 조회되지 않는다.
모든 업로드/다운로드는 이 모듈을 통해 오브젝트 스토리지로 위임한다.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class ObjectStorage:
    """MinIO/S3 클라이언트 래퍼 (thread-safe)."""

    def __init__(self) -> None:
        self._client: Optional[Minio] = None
        self._ensured = False

    @property
    def client(self) -> Minio:
        if self._client is None:
            if not settings.OBJECT_STORAGE_ACCESS_KEY or not settings.OBJECT_STORAGE_SECRET_KEY:
                raise RuntimeError(
                    "OBJECT_STORAGE_ACCESS_KEY / OBJECT_STORAGE_SECRET_KEY 가 설정되지 않았습니다. "
                    "K8s Secret 또는 .env 로 주입하세요."
                )
            self._client = Minio(
                settings.OBJECT_STORAGE_ENDPOINT,
                access_key=settings.OBJECT_STORAGE_ACCESS_KEY,
                secret_key=settings.OBJECT_STORAGE_SECRET_KEY,
                secure=settings.OBJECT_STORAGE_SECURE,
                region=settings.OBJECT_STORAGE_REGION,
            )
        return self._client

    @property
    def bucket(self) -> str:
        return settings.OBJECT_STORAGE_BUCKET

    def ensure_bucket(self) -> None:
        """버킷 존재 보장 (첫 호출 시 lazy)."""
        if self._ensured:
            return
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Object storage bucket created: %s", self.bucket)
            self._ensured = True
        except S3Error as e:
            logger.error("Bucket ensure failed: %s", e)
            raise

    def put_object(
        self,
        object_name: str,
        data: bytes,
        content_type: Optional[str] = None,
    ) -> None:
        """바이트 데이터를 오브젝트로 업로드."""
        self.ensure_bucket()
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )

    def get_object_bytes(self, object_name: str) -> bytes:
        """오브젝트를 메모리로 읽어 bytes 반환 (작은 파일용)."""
        self.ensure_bucket()
        resp = self.client.get_object(self.bucket, object_name)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def stream_object(self, object_name: str):
        """스트리밍 다운로드용 response 객체. 호출자가 close()/release_conn() 책임."""
        self.ensure_bucket()
        return self.client.get_object(self.bucket, object_name)

    def delete_object(self, object_name: str) -> None:
        self.ensure_bucket()
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as e:
            logger.warning("Delete object failed (ignored): %s / %s", object_name, e)

    def object_exists(self, object_name: str) -> bool:
        self.ensure_bucket()
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    def health_check(self) -> bool:
        """readyz 용 간단 헬스체크."""
        try:
            self.client.bucket_exists(self.bucket)
            return True
        except Exception:
            return False


# 프로세스 전역 싱글톤
object_storage = ObjectStorage()
