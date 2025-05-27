# BidTrack

> Sistema web para gerenciamento e acompanhamento de licitações públicas (com foco em prefeituras).

## 📝 Visão Geral

`BidTrack` é um aplicativo em Python que utiliza Streamlit, SQLModel, Pandas e Plotly. Com ele você pode:

* 📋 Cadastrar e gerenciar processos licitatórios (pregões)
* 🏷️ Registrar itens e fornecedores com orçamentos
* 📊 Acompanhar lances dos concorrentes em tempo real
* 🔍 Visualizar tendências de preços e margens

Ideal para empresas, consultorias ou municípios que monitoram licitações no Brasil.

## 🚀 Tecnologias

* **Python** 3.12+
* **Streamlit**: interface web interativa
* **SQLModel**: ORM para modelagem e acesso ao banco de dados
* **SQLite** (padrão) ou outros bancos SQL (PostgreSQL, MySQL)
* **Pandas**: manipulação de dados
* **Plotly**: gráficos interativos
* **UV da Astral**: gerenciamento de dependências e scripts de projeto

## 🗄️ Esquema do Banco de Dados

| Modelo         | Descrição                                                         |
| -------------- | ----------------------------------------------------------------- |
| **Bidding**    | Processo licitatório (pregão) com cidade e data/hora              |
| **Item**       | Item individual em um pregão, com quantidade, unidade e descrição |
| **Supplier**   | Fornecedores que fornecem orçamentos                              |
| **Competitor** | Concorrentes cujos lances são monitorados                         |
| **Quote**      | Preço e margem da sua organização por item/fornecedor             |
| **Bid**        | Preços ofertados pelos concorrentes para cada item                |

As relações many-to-many são modeladas pelas tabelas de ligação `Quote` e `Bid`.

## ⚙️ Instalação

1. **Clone o repositório**

   ```bash
   git clone https://github.com/seu-usuario/bidtrack.git
   cd bidtrack
   ```

2. **Instale as dependências com o UV**

   ```bash
   uv sync             # instala todas as dependências definidas
   ```

3. **Inicialize o banco de dados**

   ```bash
   uv run create-db      # cria o banco SQLite e as tabelas
   ```

## ▶️ Como Executar

Para iniciar a aplicação:

```bash
streamlit run src/main.py
```

* Acesse `http://localhost:8501`
* Crie um novo **processo licitatório**
* Adicione **Itens**, **Fornecedores** e **Orçamentos**
* Na aba **Concorrentes**, registre e acompanhe os **lances**
* Na seção **Análises**, visualize gráficos interativos

## 📈 Análises e Dashboards

* **Tendências de Preço**: acompanhe a evolução histórica dos valores por item.
* **Análise de Margem**: compare seus orçamentos com a média dos concorrentes.
* **Dashboard Resumido**: indicadores-chave de todos os processos ativos.

## 🤝 Contribuição

Contribuições são bem-vindas!

## 🛡️ Licença

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.
