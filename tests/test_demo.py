"""Testes automatizados para o modo de demonstração, diagnóstico e onboarding."""
from pathlib import Path
from unittest.mock import MagicMock

from Arquivos.demo_data import gerar_dados_demonstracao
from Arquivos.server.config import ServerConfig
from Arquivos.server.handler import RastreioRequestHandler
from run import executar_diagnostico


def test_gerar_dados_demonstracao_cria_arquivos_com_conteudo(tmp_path: Path):
    """Garante que gerar_dados_demonstracao gera os arquivos com dados válidos."""
    arquivos = gerar_dados_demonstracao(pasta_destino=tmp_path)

    assert "relatorio" in arquivos
    assert "atrasados" in arquivos
    assert "alert" in arquivos

    p_relatorio = Path(arquivos["relatorio"])
    p_atrasados = Path(arquivos["atrasados"])
    p_alert = Path(arquivos["alert"])

    assert p_relatorio.is_file()
    assert p_atrasados.is_file()
    assert p_alert.is_file()

    conteudo_relatorio = p_relatorio.read_text(encoding="utf-8")
    conteudo_atrasados = p_atrasados.read_text(encoding="utf-8")

    # Validações estruturais no relatório de demonstração
    assert "Modo Demonstração" in conteudo_relatorio
    assert "Pedido Tiny #41763" in conteudo_relatorio
    assert "Pedido Tiny #41732" in conteudo_relatorio
    assert "web/css/main.css" in conteudo_relatorio
    assert "web/js/app.js" in conteudo_relatorio
    assert 'data-status="em_transito"' in conteudo_relatorio
    assert 'data-status="atrasado"' in conteudo_relatorio
    assert 'data-status="aguardando_retirada"' in conteudo_relatorio

    # Validações estruturais na página de atrasados de demonstração
    assert "Pedidos Atrasados" in conteudo_atrasados
    assert "#41732" in conteudo_atrasados
    assert "RECIFE/PE" in conteudo_atrasados


def test_executar_diagnostico_retorna_zero():
    """Garante que o diagnóstico do ambiente executa sem erros."""
    raiz = Path(__file__).resolve().parent.parent
    resultado = executar_diagnostico(raiz)
    assert resultado == 0


def test_handler_post_api_demo_gera_arquivos(tmp_path: Path):
    """Garante que a rota POST /api/demo gera os dados e responde 200 com JSON."""
    handler = RastreioRequestHandler.__new__(RastreioRequestHandler)
    handler.server_config = ServerConfig(base_dir=tmp_path, html_file="relatorio_rastreio.html")
    handler.path = "/api/demo"

    # Mocks para wfile e respostas HTTP
    handler.wfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_POST()

    handler.send_response.assert_called_with(200)

    # Verifica se os arquivos foram criados no tmp_path
    assert (tmp_path / "relatorio_rastreio.html").is_file()
    assert (tmp_path / "pedidos_atrasados.html").is_file()


def test_handler_serve_onboarding_quando_relatorio_inexistente(tmp_path: Path):
    """Garante que a tela de onboarding com botão de demo é servida se não houver relatório."""
    handler = RastreioRequestHandler.__new__(RastreioRequestHandler)
    # Garante que o arquivo NÃO existe no diretório
    handler.server_config = ServerConfig(base_dir=tmp_path, html_file="relatorio_rastreio.html")

    handler.wfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler._serve_main_html()

    handler.send_response.assert_called_with(200)

    # Coleta os bytes escritos
    chamadas_write = handler.wfile.write.call_args_list
    bytes_enviados = b"".join(call[0][0] for call in chamadas_write)
    html_str = bytes_enviados.decode("utf-8")

    assert "Primeiro Acesso Detectado" in html_str
    assert "btnCarregarDemo" in html_str
    assert "Carregar Dados de Demonstração" in html_str
