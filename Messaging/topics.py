# ─── Upload flow ────────────────────────────────────────────
IMAGE_SUBMITTED             = "image.submitted"
IMAGE_RECEIVED              = "image.received"
IMAGE_VALIDATED             = "image.validated"
IMAGE_INVALID               = "image.invalid"

# ─── Image processing ───────────────────────────────────────
IMAGE_PROCESSING            = "image.processing"
IMAGE_PROCESSING_COMPLETE   = "image.processing.complete"

# ─── Document DB ────────────────────────────────────────────
ANNOTATION_STORING          = "annotation.storing"
ANNOTATION_STORED           = "annotation.stored"

# ─── Annotation ─────────────────────────────────────────────
IMAGE_ANNOTATING            = "image.annotating"
IMAGE_ANNOTATED             = "image.annotated"

# ─── Embedding + Vector DB ──────────────────────────────────
EMBEDDING_PROCESSING        = "embedding.processing"
EMBEDDING_COMPLETE          = "embedding.complete"
VECTOR_STORING              = "vector.storing"
VECTOR_STORED               = "vector.stored"

# ─── Failures ───────────────────────────────────────────────
IMAGE_FAILED                = "image.failed"
ANNOTATION_FAILED           = "annotation.failed"
EMBEDDING_FAILED            = "embedding.failed"

# ─── Search flow ────────────────────────────────────────────
QUERY_SUBMITTED             = "query.submitted"
QUERY_COMPLETED             = "query.completed"

ALL_TOPICS = [
    IMAGE_SUBMITTED,
    IMAGE_RECEIVED,
    IMAGE_VALIDATED,
    IMAGE_INVALID,
    IMAGE_PROCESSING,
    IMAGE_PROCESSING_COMPLETE,
    ANNOTATION_STORING,
    ANNOTATION_STORED,
    IMAGE_ANNOTATING,
    IMAGE_ANNOTATED,
    EMBEDDING_PROCESSING,
    EMBEDDING_COMPLETE,
    VECTOR_STORING,
    VECTOR_STORED,
    IMAGE_FAILED,
    ANNOTATION_FAILED,
    EMBEDDING_FAILED,
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
]