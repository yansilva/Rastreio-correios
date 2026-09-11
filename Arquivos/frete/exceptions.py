"""Exceções customizadas para a consulta de frete dos Correios."""


class FreteError(Exception):
    """Exceção base para erros na consulta de frete."""
    pass


class FreteAPIError(FreteError):
    """Lançada quando a API de preço/prazo dos Correios retorna status inesperado."""

    def __init__(self, message: str, status_code: int | None = None, detalhes: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detalhes = detalhes


class FreteConnectionError(FreteError):
    """Lançada quando ocorre falha de conexão de rede na consulta de frete."""
    pass


class FreteTimeoutError(FreteError):
    """Lançada quando a chamada HTTP de frete excede o tempo limite."""
    pass


class FreteServicoIndisponivelError(FreteError):
    """Lançada quando um serviço está indisponível para a rota solicitada (HTTP 422/400)."""
    pass
