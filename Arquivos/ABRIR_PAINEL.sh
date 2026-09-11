#!/bin/bash
# Como o script agora está dentro de Arquivos/, basta se mover para onde ele está e executar o servidor
cd "$(dirname "$0")"
python3 servidor_rastreio.py
