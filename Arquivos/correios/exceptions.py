"""Exceções customizadas para a integração com as APIs dos Correios."""

class CorreiosError(Exception):
    """Exceção base para erros na integração com os Correios."""
    pass


class CorreiosAuthError(CorreiosError):
    """Lançada quando ocorre erro de autenticação (credenciais inválidas, ausentes ou token rejeitado)."""
    pass


class CorreiosAPIError(CorreiosError):
    """Lançada quando a API dos Correios retorna status de erro ou código HTTP inesperado."""
    def __init__(self, message: str, status_code: int | None = None, detalhes: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detalhes = detalhes


class CorreiosConnectionError(CorreiosError):
    """Lançada quando ocorre uma falha de conexão de rede ou resolução DNS com os Correios."""
    pass


class CorreiosTimeoutError(CorreiosError):
    """Lançada quando a chamada HTTP aos Correios excede o tempo limite estabelecido."""
    pass
