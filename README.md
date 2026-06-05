<<<<<<< HEAD
# fmo_keys
Aplicação para controle de chaves e relatórios detalhados.
=======
# key-manager-flet

App em Python com Flet + SQLite para o **Claviculario FMO** (99 chaves pre-cadastradas).

## Recursos

- 99 chaves do claviculario FMO carregadas automaticamente na primeira execucao.
- Cadastro de chaves extras (campo discreto no rodape).
- Registro do ultimo a utilizar.
- Remover uso da chave (libera registro do usuario vinculado).
- Gravacao de data, hora e dia do ultimo uso.
- Busca/filtro por nome de chave.
- Busca/filtro por ultimo usuario e dia.
- Botao para limpar filtros rapidamente.
- Ordenacao por nome, ultimo usuario e data/hora.
- Paginacao com 10/20/50 itens e navegacao entre paginas.
- Edicao e exclusao de chaves.
- Exportacao dos registros para CSV.
- Dashboard com totais e ultimas movimentacoes.
- Interface com labels e icones para facilitar a visualizacao.

## Como rodar

1. Criar ambiente virtual:
   - Windows (PowerShell): `python -m venv .venv`
2. Ativar ambiente virtual:
   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
3. Instalar dependencias:
   - `pip install -r requirements.txt`
4. Executar:
   - `flet run main.py`
>>>>>>> e922bff (Primeiro commit do projeto Flet)
