"""Modelos de dados para resultados da consulta de frete."""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


def validar_cep(cep: str) -> bool:
    """Valida se o CEP possui formato aceitável (8 dígitos, com ou sem hífen).

    Aceita: '05617010', '05617-010'
    Rejeita: '', '0561', 'abcdefgh', '00000000'
    """
    if not cep or not isinstance(cep, str):
        return False
    limpo = cep.replace("-", "").replace(".", "").replace(" ", "").strip()
    if not re.fullmatch(r"\d{8}", limpo):
        return False
    # CEP com todos os dígitos iguais a 0 é inválido
    if limpo == "00000000":
        return False
    return True


def normalizar_cep(cep: str) -> str:
    """Remove formatação do CEP, retornando apenas 8 dígitos.

    Levanta ValueError se o CEP for inválido.
    """
    if not validar_cep(cep):
        raise ValueError(f"CEP inválido: '{cep}'")
    return cep.replace("-", "").replace(".", "").replace(" ", "").strip()[:8]


def validar_dimensoes(peso_gramas: int, comprimento: int, largura: int, altura: int) -> bool:
    """Valida que peso e dimensões são positivos."""
    return all(v > 0 for v in (peso_gramas, comprimento, largura, altura))


@dataclass
class OpcaoFrete:
    """Representa uma opção de frete retornada pela API dos Correios."""

    codigo: str          # Código do serviço (ex: "03220")
    nome: str            # Nome legível (ex: "SEDEX")
    disponivel: bool = False
    preco: Optional[Decimal] = None
    prazo_dias: Optional[int] = None
    msg_prazo: Optional[str] = None
    erro: Optional[str] = None

    @property
    def preco_formatado(self) -> Optional[str]:
        """Formata o preço no padrão brasileiro: R$ X.XXX,XX"""
        if self.preco is None:
            return None
        # Formata com 2 casas decimais
        valor_str = f"{self.preco:,.2f}"
        # Troca separadores: 1,234.56 → 1.234,56
        valor_str = valor_str.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_str}"

    def to_dict(self) -> dict:
        """Converte para dicionário compatível com o formato anterior do consulta_frete.py."""
        return {
            "disponivel": self.disponivel,
            "preco": float(self.preco) if self.preco is not None else None,
            "preco_fmt": self.preco_formatado,
            "prazo": self.prazo_dias,
            "msg_prazo": self.msg_prazo,
            "erro": self.erro,
        }

    @staticmethod
    def parse_preco(valor_str: str) -> Optional[Decimal]:
        """Converte string de preço da API dos Correios para Decimal.

        A API retorna valores como '29.90' ou '1.234,56'.
        O padrão observado: ponto como separador de milhar, vírgula como decimal.
        """
        if not valor_str or valor_str.strip() == "0":
            return None
        try:
            # Remove pontos de milhar e troca vírgula por ponto decimal
            normalizado = valor_str.replace(".", "").replace(",", ".")
            valor = Decimal(normalizado)
            if valor <= 0:
                return None
            return valor
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def parse_prazo(valor) -> Optional[int]:
        """Converte valor de prazo da API para inteiro.

        Aceita int, float, string numérica. Retorna None para valores inválidos.
        """
        if valor is None:
            return None
        try:
            prazo = int(float(valor))
            return prazo if prazo > 0 else None
        except (ValueError, TypeError):
            return None
