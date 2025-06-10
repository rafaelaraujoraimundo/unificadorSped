# 🧾 Sistema de Unificação SPED

**Versão:** 1.12  
**Desenvolvido por:** Rafael Araujo  
**Empresa:** ComBio S/A

---

## 📌 Visão Geral

Este sistema tem como objetivo **unificar arquivos SPED Fiscal** de diferentes períodos ou origens, garantindo consistência, organização e padronização dos dados fiscais. Desenvolvido com **Python e PyQt5**, o programa oferece uma interface amigável e intuitiva para facilitar a seleção, união e exportação dos arquivos SPED.

---

## 💻 Funcionalidades

- Seleção de um **arquivo principal** e múltiplos **arquivos secundários**.
- Análise e unificação conforme regras específicas para cada bloco do SPED.
- Processamento dedicado para blocos críticos como:
  - **Blocos 0200, 0205, 0220:** ordenação por `COD_ITEM` com preservação de estrutura.
  - **Bloco G110:** soma de campos selecionados, com fixação de campos não somáveis.
  - **Blocos E100 a E999, C, D, H, K:** regras específicas de soma, exclusão ou ordenação.
- Reorganização automática de blocos no final da unificação (exceto blocos 0200, 0205 e 0220 que preservam sua posição lógica).
- Geração correta dos blocos de encerramento (`0990`, `1990`, `9990`, `9999`) com contadores atualizados.
- Interface gráfica via **PyQt5** e empacotamento via **cx_Freeze** para distribuição como `.exe`.

---

## 🧰 Requisitos

- Python 3.8+
- PyQt5
- cx_Freeze

---

## ▶️ Execução

### Ambiente de Desenvolvimento

```bash
python gui_sped.py
```

### Executável (.exe)

O instalador gera o arquivo `gui_sped.exe` com o ícone personalizado (`icon.ico`).

---

## 📂 Estrutura dos Arquivos

| Arquivo                 | Descrição |
|-------------------------|-----------|
| `gui_sped.py`           | Interface gráfica principal (PyQt5). |
| `unifica_sped.py`       | Lógica de processamento e unificação dos arquivos SPED. |
| `setup.py`              | Script para geração do executável via `cx_Freeze`. |
| `icon.ico`              | Ícone da aplicação. |
| `logo.png`              | Logo exibida na aplicação. |
| `comandos`              | Arquivo auxiliar de comandos (uso interno). |

---

## 📚 Regras de Unificação por Bloco SPED

### 🔹 Bloco 0 – Abertura
- Blocos únicos.
- `0005`: somente do primeiro arquivo.
- `0500`: linhas únicas.
- `0990`: contagem real das linhas do bloco.

### 🔹 Blocos 0200, 0205, 0220
- Agrupados por `COD_ITEM`.
- Ordem pela primeira ocorrência.
- Inseridos antes do primeiro `0300`.

### 🔹 Bloco 0300 e 0305
- `0305` colado ao `0300` relacionado.

### 🔹 Bloco 0400
- Reorganizado automaticamente.

### 🔹 Bloco 0500
- Inserido após `0460`, antes de `0600`.

### 🔹 Bloco C
- `C500`, `C590` no fim do bloco.
- `C990`: recontado.

### 🔹 Bloco D
- Idêntico ao bloco C em regra.

### 🔹 Bloco E
- Sub-blocos com regras de soma:
  - `E110`: soma campos numéricos.
  - `E111`: soma do quarto campo.
  - `E116`: soma do terceiro campo.
  - `E210`: campos somados, campo fixo 0.
  - `E510`: soma por chave.
- `E100`, `E500`, `E520`: do primeiro arquivo.

### 🔹 Bloco G
- Apenas `G110` (soma campos 4, 5, 9+) e `G125`.
- Campos fixos preservados.

### 🔹 Bloco H
- `H005`: soma por data.
- `H010`: cópia integral.
- `H990`: recontado.

### 🔹 Bloco K
- `K010`, `K100`: primeira ocorrência.
- `K200`: soma campo 4 por chave.
- `K230`, `K235`: preservam ordem original.

### 🔹 Bloco 1
- `1990`: contagem real.

### 🔹 Bloco 9
- `9001`, `9900`, `9990`, `9999`: gerados automaticamente com contadores.

---

## 📬 Contato

**Rafael Araujo**  
📧 rafael.araujo@combio.com.br  
🔖 Versão atual: 1.12  
🗓️ Atualizado em: 2025

---

## 🛡️ Licença

Este sistema é de uso interno da ComBio S/A. 

