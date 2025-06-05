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

## 🗄️ Database Migrations (Alembic)

This project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage database schema changes. This is essential now that the project is in production to avoid data loss.

**Important**: Before running any Alembic commands, ensure your `DATABASE_URL` environment variable is correctly set to point to your target database (development or production). Alembic commands should be run from the project root directory, as this is where `alembic.ini` is now located.

### Key Commands:

1.  **Generating a New Migration Script:**

    After you make changes to your `SQLModel` definitions in `src/db/models.py` (e.g., add a new table, add/remove a column, change a data type), you need to generate a migration script:
    ```bash
    # Ensure you are in the project root directory
    alembic revision -m "short_description_of_your_change" --autogenerate
    # Example: alembic revision -m "add_link_column_to_quote_table" --autogenerate
    ```
    This command will compare your models against the current state of the database (as Alembic understands it) and generate a new script in `alembic/versions/`. Always review the generated script to ensure it matches your intended changes.

2.  **Applying Migrations:**

    To apply pending migrations to your database (i.e., update the database schema to the latest version):
    ```bash
    # Ensure you are in the project root directory
    alembic upgrade head
    ```
    `head` refers to the latest revision. You can also upgrade or downgrade to specific revisions.

3.  **Checking Current Database Revision:**

    To see the current revision of your database:
    ```bash
    # Ensure you are in the project root directory
    alembic current
    ```

4.  **Downgrading a Migration (Use with caution):**

    To revert the last applied migration:
    ```bash
    # Ensure you are in the project root directory
    alembic downgrade -1
    ```
    Or to a specific revision:
    ```bash
    # Ensure you are in the project root directory
    alembic downgrade <revision_id>
    ```
    Downgrading can be risky, especially if the migration involves data loss. Always back up your production database before performing downgrades or complex upgrades.

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

3. **Setup and Migrate the Database**

   Ensure the `DATABASE_URL` environment variable is set to your target database.
   Then, apply migrations:
   ```bash
   # Ensure you are in the project root directory
   alembic upgrade head  # Applies all pending migrations
   ```
   The `uv run create-db` script might still be useful for other initialization tasks, but schema creation is now handled by Alembic.

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
