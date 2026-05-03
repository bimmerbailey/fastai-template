import structlog.stdlib
from faststream.nats import NatsRouter, PullSub
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.documents.models import Document
from fastai.embeddings.models import Embedding
from fastai.embeddings.schemas import EmbeddingCreate
from fastai.events import DOCUMENT_STREAM, SUBJECT_DOCUMENT_UPLOADED
from fastai.events.schemas import DocumentUploaded
from fastai.subscribers_v1.dependencies import (
    EngineDep,
    ExtractionDep,
    KnowledgeBaseDep,
    StorageServiceDep,
)

logger = structlog.stdlib.get_logger(__name__)

router = NatsRouter()


@router.subscriber(
    SUBJECT_DOCUMENT_UPLOADED,
    stream=DOCUMENT_STREAM,
    durable="embedding-worker",
    pull_sub=PullSub(),
)
async def process_document(
    event: DocumentUploaded,
    engine: EngineDep,
    extraction: ExtractionDep,
    kb: KnowledgeBaseDep,
    storage: StorageServiceDep,
) -> None:
    """Process a document upload event: extract text, chunk, embed.

    Steps:
        1. Mark document as "processing"
        2. Check content type support
        3. Download file from S3
        4. Extract text and chunk
        5. Embed each chunk
        6. Mark document as "completed"

    On error, marks the document as "failed".
    """

    document_id = event.document_id
    logger.info("Processing document", document_id=str(document_id))

    async with AsyncSession(engine) as session:
        doc = await Document.get(session, document_id)
        if doc is None:
            logger.error("Document not found, skipping", document_id=str(document_id))
            return
        await doc.update_embedding_status(session, "processing")

        try:
            # Check content type support
            if not Document.is_extractable(event.content_type):
                logger.info(
                    "Unsupported content type, skipping",
                    document_id=str(document_id),
                    content_type=event.content_type,
                )
                await doc.update_embedding_status(session, "skipped")
                return

            # Download file from S3
            file_bytes = await storage.download_bytes(event.storage_path)

            # Extract text and chunk
            chunks = await extraction.extract_and_chunk(file_bytes, event.filename)

            if not chunks:
                logger.warning(
                    "No text extracted from document",
                    document_id=str(document_id),
                )
                await doc.update_embedding_status(session, "skipped")
                return

            # Delete any existing embeddings for this document (re-processing)
            await Embedding.delete_by_source(session, "document", document_id)

            # Embed each chunk
            for chunk_index, chunk_text in enumerate(chunks):
                embedding_in = EmbeddingCreate(
                    source_type="document",
                    source_id=document_id,
                    chunk_text=chunk_text,
                    chunk_index=chunk_index,
                    extra_metadata={
                        "filename": event.filename,
                        "content_type": event.content_type,
                        "chunk_index": chunk_index,
                        "total_chunks": len(chunks),
                    },
                )
                result = await kb.embedder.embed_documents(chunk_text)
                vector = list(result.embeddings[0])
                await Embedding.upsert(session, embedding_in, vector, kb.model_name)

            logger.info(
                "Document processing completed",
                document_id=str(document_id),
                chunks_embedded=len(chunks),
            )

            await doc.update_embedding_status(session, "completed")

        except Exception:
            logger.exception(
                "Failed to process document",
                document_id=str(document_id),
            )
            # Use a fresh session — the original may be in a broken state
            # after a failed commit.
            async with AsyncSession(engine) as err_session:
                doc = await Document.get(err_session, document_id)
                if doc:
                    await doc.update_embedding_status(err_session, "failed")
