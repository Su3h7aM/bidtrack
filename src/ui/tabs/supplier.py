import streamlit as st
import pandas as pd  # Though not directly used in this config, good for consistency if hooks were added
from ..components.entity_manager import display_entity_management_ui
# from db.repositories import SupplierRepository # For type hinting if needed


def display_suppliers_tab(
    supplier_repo,
):  # Add type hint: supplier_repo: SupplierRepository
    """Displays the content for the Suppliers management tab."""

    supplier_cols_to_display = ["name", "website", "email", "phone", "desc"]

    supplier_column_config = {
        "id": st.column_config.NumberColumn(
            "ID", disabled=True, help="ID único do fornecedor no sistema."
        ),
        "name": st.column_config.TextColumn(
            "Nome", required=True, help="Nome do fornecedor."
        ),
        "website": st.column_config.TextColumn(
            "Website", help="Website do fornecedor (opcional)."
        ),
        "email": st.column_config.TextColumn(
            "Email", help="Email de contato do fornecedor (opcional)."
        ),
        "phone": st.column_config.TextColumn(
            "Telefone", help="Telefone de contato (opcional)."
        ),
        "desc": st.column_config.TextColumn(
            "Descrição", help="Descrição ou observações sobre o fornecedor (opcional)."
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Criado em",
            format="YYYY-MM-DD HH:mm",
            disabled=True,
            help="Data de criação do registro.",
        ),
        "updated_at": st.column_config.DatetimeColumn(
            "Atualizado em",
            format="YYYY-MM-DD HH:mm",
            disabled=True,
            help="Data da última atualização do registro.",
        ),
    }
    display_entity_management_ui(
        repository=supplier_repo,
        entity_name_singular="Fornecedor",
        entity_name_plural="Fornecedores",
        columns_to_display=supplier_cols_to_display,
        column_config=supplier_column_config,
        search_columns=["name", "website", "email", "phone", "desc"],
        custom_search_label="Buscar Fornecedores (por nome, website, email, telefone, descrição):",
        editable_columns=["name", "website", "email", "phone", "desc"],
        required_fields=["name"],
        editor_key_suffix="suppliers",
        is_editable=False,  # Set to read-only
    )
