"""Ponto de entrada principal do Rastreio-correios.

Inicia o servidor web local e disponibiliza o painel operacional de rastreamento,
auditoria de entregas e cotação de frete.

Uso:
    python run.py                   # Execução normal
    python run.py --demo            # Execução em modo demonstração (com dados mockados)
    python run.py --check           # Diagnóstico do ambiente e variáveis
    python run.py --port 8080       # Customização de porta
    python run.py --no-browser      # Não abre o navegador automaticamente
"""
import argparse
import os
import sys
from pathlib import Path

# Ajusta encoding de terminal para evitar erros no Windows cp1252
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Assegura que o diretório 'Arquivos' esteja no PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
DIR_ARQUIVOS = BASE_DIR / "Arquivos"

if str(DIR_ARQUIVOS) not in sys.path:
    sys.path.insert(0, str(DIR_ARQUIVOS))

from server import ServerConfig, iniciar_servidor


def executar_diagnostico(base_dir: Path) -> int:
    """Executa diagnóstico do ambiente, dependências e configurações."""
    print("=" * 65)
    print("DIAGNOSTICO DO AMBIENTE - Rastreio-correios")
    print("=" * 65)

    erros = 0
    avisos = 0

    # 1. Versão do Python
    py_ver = sys.version_info
    print(f"\n[1/4] Versao do Python: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    if py_ver >= (3, 11):
        print("      [OK] Compativel (Requisito: Python 3.11+)")
    else:
        print("      [X] Incompativel: O projeto requer Python 3.11 ou superior.")
        erros += 1

    # 2. Dependências de Produção
    print("\n[2/4] Verificando dependencias essenciais...")
    dependencias = [
        ("requests", "Requisicoes HTTP para APIs"),
        ("dotenv", "Leitura de variaveis de ambiente (.env)"),
    ]
    for modulo, desc in dependencias:
        try:
            __import__(modulo)
            print(f"      [OK] {modulo:<12} - {desc}")
        except ImportError:
            print(f"      [X]  {modulo:<12} - NAO INSTALADO ({desc})")
            erros += 1

    # Ferramentas de desenvolvimento (opcionais)
    dev_deps = [
        ("pytest", "Execucao de testes automatizados"),
        ("ruff", "Linter e formatador de codigo"),
    ]
    for modulo, desc in dev_deps:
        try:
            __import__(modulo)
            print(f"      [OK] {modulo:<12} - {desc} (Dev)")
        except ImportError:
            print(f"      [!]  {modulo:<12} - Nao instalado ({desc}) [Opcional]")
            avisos += 1

    # 3. Variáveis de Ambiente
    print("\n[3/4] Verificando arquivo de configuracao (.env)...")
    caminho_env = base_dir / ".env"
    if caminho_env.is_file():
        print(f"      [OK] Arquivo .env encontrado em: {caminho_env}")
        from dotenv import load_dotenv

        load_dotenv(caminho_env)

        chaves = [
            ("TOKEN_TINY", "Autenticacao no Tiny ERP"),
            ("ID_CORREIOS", "ID de acesso Correios Cws"),
            ("CONTRATO", "Numero do Contrato Correios"),
            ("CODIGO_ACESSO", "Codigo de Acesso Correios"),
            ("CEP_ORIGEM", "CEP de Origem para Cotacao"),
        ]
        preenchidas = 0
        for chave, desc in chaves:
            val = os.getenv(chave, "").strip()
            if val and val != "seu_token_aqui" and not val.startswith("seu_"):
                print(f"      [OK] {chave:<14} - Configurado")
                preenchidas += 1
            else:
                print(f"      [!]  {chave:<14} - Pendente ({desc})")
                avisos += 1

        if preenchidas == len(chaves):
            print("      [OK] Todas as credenciais de producao estao configuradas!")
        else:
            print("      [INFO] Credenciais incompletas: Use 'python run.py --demo' para testar.")
    else:
        print("      [!]  Arquivo .env nao encontrado.")
        print("      [INFO] Copie .env.example para .env ou execute com 'python run.py --demo'.")
        avisos += 1

    # 4. Arquivos do Frontend e Relatórios
    print("\n[4/4] Verificando camada de visualizacao e relatorios...")
    web_assets = [
        base_dir / "web" / "css" / "main.css",
        base_dir / "web" / "css" / "components.css",
        base_dir / "web" / "js" / "app.js",
        base_dir / "web" / "js" / "dashboard.js",
        base_dir / "web" / "js" / "logs.js",
    ]
    assets_ok = all(a.is_file() for a in web_assets)
    if assets_ok:
        print("      [OK] Todos os assets modulares do frontend (web/) estao presentes.")
    else:
        print("      [X]  Assets do frontend corrompidos ou ausentes.")
        erros += 1

    relatorio = base_dir / "relatorio_rastreio.html"
    if relatorio.is_file():
        print(f"      [OK] Relatorio ativo disponivel: {relatorio.name}")
    else:
        print("      [INFO] Nenhum relatorio gerado ainda (o servidor exibira tela de boas-vindas).")

    # Resumo
    print("\n" + "=" * 65)
    if erros == 0:
        print("[SUCESSO] DIAGNOSTICO CONCLUIDO COM SUCESSO! Ambiente operacional pronto.")
        if avisos > 0:
            print(f"          ({avisos} aviso(s) nao impeditivos detectados)")
        print("=" * 65)
        return 0
    else:
        print(f"[FALHA] DIAGNOSTICO APONTOU {erros} ERRO(S) IMPEDITIVO(S).")
        print("        Execute: pip install -r requirements.txt")
        print("=" * 65)
        return 1


def main() -> None:
    """Ponto de entrada com suporte a argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Servidor web e painel de controle do Rastreio-correios."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Gera dados sintéticos de demonstração e inicia o servidor imediatamente.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Executa diagnóstico do ambiente, dependências e configurações sem iniciar o servidor.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Porta TCP na qual o servidor responderá (padrão: SERVER_PORT do .env ou 8000).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Endereço de rede do servidor (padrão: SERVER_HOST do .env ou 127.0.0.1).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Não abre o navegador web automaticamente ao iniciar.",
    )

    args = parser.parse_args()

    # Comando 1: Diagnóstico
    if args.check:
        sys.exit(executar_diagnostico(BASE_DIR))

    # Comando 2: Modo Demonstração
    if args.demo:
        print("=" * 65)
        print("🚀 GERANDO DADOS DE DEMONSTRAÇÃO (MODO PORTFÓLIO)...")
        print("=" * 65)
        try:
            from demo_data import gerar_dados_demonstracao

            arquivos = gerar_dados_demonstracao(BASE_DIR)
            print("✅ Relatórios de demonstração gerados com sucesso:")
            for tipo, caminho in arquivos.items():
                print(f"   - {tipo}: {caminho}")
        except Exception as exc:
            print(f"❌ Erro ao gerar demonstração: {exc}")
            sys.exit(1)

    # Configuração do Servidor
    config = ServerConfig.from_env(base_dir=BASE_DIR)
    if args.port:
        config.port = args.port
    if args.host:
        config.host = args.host

    abrir_navegador = not args.no_browser
    iniciar_servidor(config=config, abrir_browser=abrir_navegador)


if __name__ == "__main__":
    main()
