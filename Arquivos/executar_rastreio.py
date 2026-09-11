import importlib
import os

import consulta_correios  # type: ignore
import tiny_rastreio  # type: ignore


def main():
    # Força o recarregamento dos módulos caso o servidor esteja rodando continuamente
    importlib.reload(tiny_rastreio)
    importlib.reload(consulta_correios)
    print("="*60)
    print("INICIANDO AUTOMACAO DE RASTREIO (TINY + CORREIOS)")
    print("="*60)

    # 1. Buscar pedidos no Tiny
    print("\n[PASSO 1/2] Integrando com Tiny ERP...")
    try:
        sucesso_tiny = tiny_rastreio.processar()
        if not sucesso_tiny:
            print("Erro na etapa do Tiny. Abortando processo.")
            return
    except Exception as e:
        print(f"Erro critico ao processar Tiny: {e}")
        return

    # 2. Consultar rastreios nos Correios e Gerar Relatório
    print("\n[PASSO 2/2] Consultando Correios e Gerando Relatório HTML...")
    try:
        # Verifica se o arquivo gerado pelo Tiny existe antes de prosseguir
        caminho_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rastreios_tiny.csv")
        if os.path.exists(caminho_csv):
            consulta_correios.processar()

            print("\n[PASSO 3/3] Consultando Opções de Frete...")
            import consulta_frete
            importlib.reload(consulta_frete)
            consulta_frete.processar()

            print("\n" + "="*60)
            caminho_relatorio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorio_rastreio.html")
            print("PROCESSO CONCLUIDO COM SUCESSO!")
            print(f"Relatorio disponivel em: {caminho_relatorio}")
            print("="*60)
        else:
            print(f"⚠️ Arquivo '{caminho_csv}' não encontrado. Verifique os filtros do Tiny.")

    except Exception as e:
        print(f"Erro critico ao processar Correios: {e}")

if __name__ == "__main__":
    main()
