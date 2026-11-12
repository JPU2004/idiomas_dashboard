# LinguaGraph — Dashboard da Escola de Idiomas

## 1. Instalação
Instale Python 3.10+ e, no terminal dentro desta pasta, execute:

```bash
pip install -r requirements.txt
streamlit run app.py
```

O dashboard abre no navegador e funciona imediatamente com dados fictícios (modo demonstração).

## 2. Ativar FalkorDB (opcional)
Instale e abra o Docker Desktop. No terminal desta pasta:

```bash
docker compose up -d
python seed.py
```

No Windows PowerShell, execute:

```powershell
$env:USE_FALKORDB="1"
streamlit run app.py
```

No Linux/macOS:

```bash
USE_FALKORDB=1 streamlit run app.py
```

O dashboard passará a ler os nós e relações do grafo `EscolaIdiomas`.

## Estrutura do grafo
`(Idioma)-[:OFERECE]->(Turma)-[:MINISTRADA_POR]->(Professor)`

## Observações
- Dados fictícios para uso acadêmico.
- `seed.py` apaga os nós existentes **somente no grafo EscolaIdiomas** antes de criar os dados de exemplo. Não execute sobre dados reais que queira preservar.
- O modo de demonstração não depende do Docker nem do banco.

## 3. Grafo interativo (novo)
Abra a aba **Grafo Interativo** no dashboard. A visualização usa PyVis e mostra os nós Idioma, Turma e Professor e as relações OFERECE e MINISTRADA_POR.

Os filtros de idioma, nível e turno funcionam nas duas abas. Com `USE_FALKORDB=1`, a visualização consulta diretamente o grafo `EscolaIdiomas`; sem essa variável, exibe uma rede demonstrativa identificada como fictícia.

Para atualizar uma instalação anterior, execute novamente `pip install -r requirements.txt`. **Não execute `seed.py` novamente se quiser preservar os dados existentes.**

Se a porta 8501 estiver ocupada, execute `streamlit run app.py --server.port 8502`.
