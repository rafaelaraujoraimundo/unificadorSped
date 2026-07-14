# 🧾 Unificador SPED - Combio

Aplicação desktop (Windows) em **Python + PyQt5** que unifica múltiplos arquivos **SPED Fiscal / Contribuições** (layout `|REG|campo1|campo2|...|`) em um único arquivo `.txt`, aplicando regras específicas de deduplicação, soma e reordenação para cada bloco do leiaute, e recalculando os totalizadores de fechamento.

Desenvolvido por **Rafael Araujo** — Setor de Tecnologia da Informação, ComBio S/A.

---

## 🧰 Stack

- **Linguagem:** Python (3.10 em `__pycache__`, 3.14 no build mais recente — sem pin rígido de versão)
- **Interface gráfica:** PyQt5
- **Empacotamento para `.exe`:** cx_Freeze (`setup.py`)
- **Instalador Windows:** Inno Setup (`install_script.iss`)
- **Sem framework web, sem banco de dados, sem API** — é um utilitário desktop local que lê e escreve arquivos texto no disco.

Dependências declaradas em `requirements.txt`:
```
PyQt5
cx_Freeze
```

---

## 💻 Funcionalidades

### Interface (`gui_sped.py`)
- Seleção de **um arquivo principal** (`QFileDialog.getOpenFileName`) e de **um ou mais arquivos secundários** (`QFileDialog.getOpenFileNames`), listados em uma `QListWidget` com opção de remover itens individualmente (com confirmação).
- Botão **"Unificar Arquivos"**: valida que há arquivo principal e ao menos um secundário, pede confirmação, executa a unificação e abre um diálogo **"Salvar como"** para gravar o `.txt` resultante.
- Tratamento de erros com `QMessageBox` (mensagens de sucesso, aviso e erro).
- Menu **Ajuda → Sobre** com dados de versão/contato.
- Barra de status com nome da empresa e versão exibida.
- Ícone (`icon.ico`) e logo (`logo.png`) próprios da aplicação.

> Observação: existe um arquivo `tela_principal.py` (gerado por `pyuic5` a partir de um `TelaPrincipal.ui`), mas está vazio/sem uso — a interface real é toda construída em código dentro de `gui_sped.py`.

### Motor de unificação (`unifica_sped.py`)
A função principal `unificar_arquivos_sped(arquivos)` recebe uma lista de caminhos (o principal primeiro, seguido dos secundários) e devolve a lista de linhas do arquivo unificado. Ela lê cada arquivo com `ler_arquivo_sped` (tenta UTF-8, cai para Latin-1 em caso de erro de decodificação) e aplica, em sequência, regras específicas por bloco:

**Bloco 0 (abertura/cadastros)**
- Registros únicos do bloco 0 (deduplicados por `(registro, campo1)`), exceto os tratados à parte (`0005, 0200, 0205, 0220, 0300, 0305, 0500, 0990`).
- `0005`: copiado apenas do primeiro arquivo em que aparece, inserido logo após o `0002`.
- `0200/0205/0220`: unificados por `COD_ITEM`, agrupando cada `0200` com seus `0205`/`0220` relacionados; ordem definida pela primeira aparição do item entre todos os arquivos; bloco reinserido antes do primeiro `0300` no resultado final.
- `0300/0305`: cada `0300` é emparelhado com o `0305` imediatamente seguinte (se existir); a sequência é reinserida antes do bloco `0400` (ou ao final, se não houver `0400`).
- `0400`: mantido junto ao restante do fluxo normal de reorganização.
- `0500`: linhas deduplicadas por conteúdo integral, reinseridas depois do `0600` (código busca o marcador `0600`, inserindo antes dele).
- `0990`: recalculado ao final com a contagem real de linhas do bloco 0.

**Bloco B (parcial)**
- Apenas `B001` e `B990` são importados, e só do **arquivo principal** (primeiro da lista) — via `importar_blocos_especificos`. Os demais registros `B1xx/B2xx/...` não são copiados para o resultado.

**Bloco C**
- Todos os registros (exceto `C001`/`C990`) são mantidos; `C500` e `C590` são movidos para o final do bloco (antes do `C990`).
- `C990` recontado; se não houver nenhum registro C, gera `C001|1|` / `C990|2|` vazios.

**Bloco D**
- Respeita a hierarquia `D1** → D5** → D7** → D990`: registros são agrupados por prefixo (`D1`, `D5`, `D7`; qualquer outro cai no grupo `D1`) e concatenados nessa ordem.
- `D990` recontado; bloco vazio gera `D001|1|` / `D990|2|`.

**Bloco E**
- `E100`, `E500`, `E520`: copiados apenas do primeiro arquivo em que aparecem.
- `E110`: soma campo a campo (numérico) de todas as ocorrências.
- `E111`: soma o 4º campo; demais campos vêm da primeira ocorrência.
- `E116`: soma o 3º campo; demais campos preservados da primeira ocorrência.
- `E200/E210`: agrupados por linha `E200`; os valores do `E210` correspondente são somados e o campo logo após `E210` é fixado em `0`.
- `E510`: somado por chave (`registro` + campos 2 e 3).
- `E990` recalculado; bloco vazio gera `E001|1|` / `E990|2|`.
- Demais registros do bloco E (`E200` isolado sem `E210`, etc.) não descritos acima são descartados.

**Bloco G (parcial)**
- Apenas `G110`, `G125` (com seus filhos `G130`/`G140` imediatamente seguintes) são mantidos.
- `G110`: soma os campos 4, 5 e do 9 em diante (arredondados a 2 casas); campos 1–3 e 6–8 ficam fixos (valores da primeira ocorrência).
- `G990` recalculado; bloco vazio gera `G001|1|` / `G990|2|`.
- Demais registros do bloco G não são copiados.

**Bloco H**
- `H005`: soma o 3º campo (valor) por chave = data (2º campo); campo final fixado em `01`.
- `H010`: todas as ocorrências copiadas integralmente.
- `H990` recalculado conforme quantidade real de linhas do bloco; bloco vazio gera `H001|1|` / `H990|2|`.

**Bloco K**
- `K010` e `K100`: primeira ocorrência de cada um (de qualquer arquivo).
- `K200`: soma o 4º campo agrupando por chave (campos 2 e 3); demais campos fixados (`0` e vazio).
- `K230`/`K235`: todas as ocorrências copiadas, preservando a ordem original de leitura.
- `K990` recalculado; bloco vazio gera `K001|1|` / `K990|2|`.

**Bloco 1 (parcial)**
- Apenas `1001` e `1010` são importados, e só do **arquivo principal** — via a mesma `importar_blocos_especificos` usada para o bloco B. Demais registros `1xxx` não são copiados.
- `1990`: recalculado com a contagem real de linhas do bloco 1 no resultado.

**Bloco 9 (fechamento, gerado do zero)**
- `9001|0|` fixo.
- `9900`: um registro por tipo de campo (`REG`) presente no arquivo final, com a contagem de ocorrências, mais os totalizadores fixos para `9001`, `9900`, `9990` e `9999`.
- `9990`: contagem de linhas do próprio bloco 9.
- `9999`: total de linhas do arquivo unificado inteiro (gerado por último).

**Blocos não suportados / não copiados**
- Os blocos `A`, `F`, `I`, `J`, `L`, `M`, `N`, `O`, `P`, `Q`, `R`, `S`, `T` **não têm nenhuma regra de processamento** — registros desses blocos presentes nos arquivos de entrada são descartados e não aparecem no arquivo final (não há função `processar_bloco_*` para eles).

**Reorganização final**
- `organizar_blocos` reagrupa todas as linhas na ordem `0, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, 1, 9` (mesmo que a maioria desses blocos esteja sempre vazia, por não terem processamento dedicado).
- Os registros `0200/0205/0220` são retirados antes dessa reorganização e reinseridos manualmente logo antes do primeiro `0300` do resultado, preservando a estrutura hierárquica do item.
- Uma segunda passada (`totalizar_blocos_X990`) percorre o arquivo já montado somando novamente a ocorrência de linhas cujo registro termina em `990` e acrescenta totalizadores extras ao final (função herdada de versões anteriores; na prática atua sobre os blocos que ainda restarem).

### Empacotamento / distribuição
- `setup.py` usa **cx_Freeze** para gerar `gui_sped.exe` (ícone `icon.ico`), incluindo as DLLs e plugins do Qt5 necessários (`Qt5Core`, `Qt5Gui`, `Qt5Widgets`, pasta `plugins`).
- `install_script.iss` (Inno Setup) empacota o build (`build/exe.win-amd64-3.14/...`) em um instalador Windows (`Setup_v{versão}_Unificação SPED - Combio.exe`), em português, com ícone de área de trabalho opcional.
- A pasta `Output/` guarda o histórico de instaladores já gerados (v1.0 até v1.15, incluindo variações de nome do produto ao longo do tempo).
- O arquivo `comandos` documenta, como anotação, os comandos usados para regenerar a UI (`pyuic5`) e para buildar o `.exe` (`python setup.py build`).

### Testes
- `claude/teste_bloco_d.py`: script de teste manual (não integrado a um runner tipo pytest) que monta arquivos SPED temporários e valida que `processar_bloco_d` respeita a hierarquia `D001 → D1** → D5** → D7** → D990` e que nenhum registro esperado é perdido.

---

## 🏗️ Arquitetura / Estrutura de arquivos

```
unificadorSped/
├── gui_sped.py                # Interface gráfica (PyQt5) — ponto de entrada da aplicação
├── unifica_sped.py            # Lógica de leitura, unificação por bloco e escrita dos arquivos SPED
├── tela_principal.py          # Stub gerado por pyuic5 a partir de TelaPrincipal.ui (não utilizado)
├── setup.py                   # Empacotamento do .exe via cx_Freeze
├── install_script.iss         # Script do instalador Windows (Inno Setup)
├── requirements.txt           # Dependências Python (PyQt5, cx_Freeze)
├── icon.ico / logo.png        # Identidade visual da aplicação
├── comandos                   # Anotações dos comandos de build/uso (uso interno)
├── claude/
│   └── teste_bloco_d.py       # Teste manual da regra do Bloco D
├── build/                     # Saída do cx_Freeze (gui_sped.exe + libs/Qt) — gerado, não versionado
├── Output/                    # Instaladores .exe já gerados (histórico de versões v1.0–v1.15)
├── Unificador SPED/           # Pasta de saída vazia (destino de instalação/uso local)
├── Unificador SPED - Combio/  # Pasta de saída vazia (idem, versão renomeada)
├── SPED_Application.egg-info/ # Metadados de empacotamento (nome "SPED-Application", versão 1.5)
└── venv/                      # Ambiente virtual Python local
```

Fluxo de execução: `gui_sped.py` importa `unificar_arquivos_sped` e `escrever_arquivo_sped` de `unifica_sped.py` → usuário escolhe arquivos via diálogo → clique em "Unificar" chama o motor de unificação → resultado é salvo em disco via diálogo "Salvar como".

---

## ▶️ Como rodar / usar

### Ambiente de desenvolvimento
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python gui_sped.py
```

### Uso (passo a passo na interface)
1. Clique em **"Selecionar Arquivo Principal"** e escolha o `.txt` do SPED que servirá de base (dele vêm os blocos `B001/B990`, `1001/1010`, `E100/E500/E520`, entre outros "primeira ocorrência").
2. Clique em **"Adicionar Arquivos Secundários"** e selecione um ou mais arquivos `.txt` adicionais a unificar.
3. (Opcional) Selecione um item na lista e clique em **"Remover Arquivo Selecionado"** para tirá-lo da unificação.
4. Clique em **"Unificar Arquivos"**, confirme a ação e, no diálogo que abre, escolha o caminho/nome do arquivo unificado de saída.
5. Ao concluir, é exibida a mensagem de sucesso com o caminho do arquivo gerado.

### Gerar o executável (.exe)
```bash
pip install cx_Freeze
python setup.py build
```
Gera `build/exe.win-amd64-<versão>/gui_sped.exe` com as DLLs do Qt5 necessárias.

### Gerar o instalador Windows
Compilar `install_script.iss` no Inno Setup (usa como fonte os arquivos da pasta `build/exe.win-amd64-3.14/`), gerando `Setup_v{versão}_Unificação SPED - Combio.exe` em `Output/`.

---

## ⚙️ Variáveis de ambiente / parâmetros

Não há variáveis de ambiente, arquivo de configuração ou argumentos de linha de comando — é uma aplicação 100% gráfica. Os únicos "parâmetros" de entrada são os caminhos de arquivo escolhidos pelo usuário nos diálogos:

- **Arquivo principal:** um único `.txt` (obrigatório).
- **Arquivos secundários:** um ou mais `.txt` (obrigatório ao menos um).
- **Arquivo de saída:** caminho/nome escolhido no diálogo "Salvar como" ao final da unificação.

---

## 📥 Entradas e 📤 Saídas

**Entrada:** um ou mais arquivos texto (`.txt`) no leiaute SPED Fiscal/Contribuições — registros delimitados por pipe (`|REG|campo1|campo2|...|`), um registro por linha, terminados em `\n`. A leitura tenta `UTF-8` primeiro e usa `Latin-1` como fallback caso haja erro de decodificação.

**Saída:** um único arquivo `.txt` no mesmo leiaute, contendo:
- Os registros unificados/deduplicados/somados por bloco, conforme as regras descritas acima;
- Blocos de encerramento recalculados (`0990`, `C990`, `D990`, `E990`, `G990`, `H990`, `K990`, `1990`, `9990`, `9999`) com as contagens reais do arquivo final;
- Bloco `9` (`9001`, `9900...`, `9990`) gerado do zero com base na contagem de registros do arquivo final;
- Blocos sem regra de processamento definida (`A, F, I, J, L, M, N, O, P, Q, R, S, T` e a maior parte de `B` e `1`) **não são incluídos** na saída.

Não há persistência em banco de dados nem chamadas de rede — toda a operação é local, em memória, sobre os arquivos selecionados.

---

## 📬 Contato

**Rafael Araujo**
📧 rafael.araujo@combio.com.br
🔖 Versões distribuídas: `Output/` vai de v1.0 a v1.15 (instalador mais recente conforme `install_script.iss`); `setup.py`, `gui_sped.py` e `install_script.iss` estão alinhados na versão `1.15` — os números de versão ainda não estão centralizados em um único lugar do repositório.

---

## 🛡️ Licença

Uso interno da ComBio S/A.
