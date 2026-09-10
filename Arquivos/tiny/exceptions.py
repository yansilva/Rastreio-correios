"""Exceções customizadas para a integração com a API do Tiny ERP."""

class TinyError(Exception):
    """Exceção base para erros na integração com o Tiny ERP."""
    pass


class TinyAuthError(TinyError):
    """Lançada quando o token de autenticação não foi configurado ou é inválido."""
    pass


class TinyAPIError(TinyError):
    """Lançada quando a API do Tiny retorna status de erro ou código HTTP inesperado."""
    def __init__(self, message: str, status_code: int | None = None, detalhes: list | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detalhes = detalhes or []


class TinyConnectionError(TinyError):
    """Lançada quando ocorre uma falha de conexão de rede com a API do Tiny."""
    pass


class TinyTimeoutError(TinyError):
    """Lançada quando a requisição à API do Tiny excede o tempo limite estabelecido."""
    pass
