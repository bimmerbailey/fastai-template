class EmbeddingError(Exception):
    pass


class EmbeddingNotFoundError(EmbeddingError):
    pass


class EmbeddingProviderError(EmbeddingError):
    pass
