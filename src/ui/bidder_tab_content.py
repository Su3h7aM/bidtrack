import streamlit as st
import pandas as pd # For consistency
from ui.generic_entity_management import display_entity_management_ui
# from db.repositories import BidderRepository # For type hinting

def display_bidders_tab(bidder_repo): # bidder_repo: BidderRepository
    """Displays the content for the Bidders management tab."""

    bidder_cols_to_display = ["name", "website", "email", "phone", "desc"]

    bidder_column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True, help="ID único do licitante."),
        "name": st.column_config.TextColumn("Nome", required=True, help="Nome do licitante."),
        "website": st.column_config.TextColumn("Website", help="Website do licitante (opcional)."),
        "email": st.column_config.TextColumn("Email", help="Email de contato (opcional)."),
        "phone": st.column_config.TextColumn("Telefone", help="Telefone de contato (opcional)."),
        "desc": st.column_config.TextColumn("Descrição/Observações", help="Outras informações relevantes (opcional)."),
        "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
        "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
    }
    display_entity_management_ui(
        repository=bidder_repo,
        entity_name_singular="Licitante",
        entity_name_plural="Licitantes",
        columns_to_display=bidder_cols_to_display,
        column_config=bidder_column_config,
        search_columns=["name", "website", "email", "phone", "desc"],
        custom_search_label="Buscar Licitantes (por nome, website, email, telefone, descrição):",
        editable_columns=["name", "website", "email", "phone", "desc"],
        required_fields=["name"],
        editor_key_suffix="bidders",
        is_editable=False # Set to read-only
    )
