import streamlit as st
import pandas as pd
from decimal import Decimal  # For consistency, though not directly used
from ..components.entity_manager import display_entity_management_ui
# from db.repositories import ItemRepository, BiddingRepository # For type hinting


def display_items_tab(
    item_repo, bidding_repo
):  # item_repo: ItemRepository, bidding_repo: BiddingRepository
    """Displays the content for the Items management tab."""

    # Configuration for selecting the parent Bidding
    fk_bidding_selection_config = {
        "label": "Escolha uma Licitação para ver seus Itens",
        "repository_for_options": bidding_repo,  # Passed to the function
        "options_map_config": {
            "name_col": "process_number",  # Or another representative column from Bidding model
            "extra_cols": ["city", "process_number", "mode"],  # Show city and mode
            "default_message": "Selecione uma Licitação...",
        },
        "filter_column_on_df": "bidding_id",  # This is the FK column in the Item model
        "block_if_parent_not_selected": True,  # Don't show items table if no bidding is selected
    }

    # Columns specifically for user display in st.data_editor
    item_cols_to_display = ["name", "desc", "code", "quantity", "unit", "notes"]

    item_column_config = {
        "id": st.column_config.NumberColumn(
            "ID", disabled=True, help="ID único do item."
        ),
        "name": st.column_config.TextColumn(
            "Nome do Item", required=True, help="Nome descritivo do item."
        ),
        "desc": st.column_config.TextColumn(
            "Descrição Detalhada", help="Descrição mais completa do item (opcional)."
        ),
        "code": st.column_config.TextColumn(
            "Código do Item", help="Código ou SKU do item (opcional)."
        ),
        "quantity": st.column_config.NumberColumn(
            "Quantidade",
            format="%.2f",
            min_value=0.00,
            required=True,
            help="Quantidade necessária do item.",
        ),
        "unit": st.column_config.TextColumn(
            "Unidade", required=True, help="Unidade de medida do item (ex: un, kg, m²)."
        ),
        "notes": st.column_config.TextColumn(
            "Observações", help="Observações adicionais sobre o item (opcional)."
        ),
        "bidding_id": st.column_config.NumberColumn(
            "ID da Licitação",
            disabled=True,
            help="ID da licitação à qual este item pertence.",
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Criado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
        "updated_at": st.column_config.DatetimeColumn(
            "Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
    }

    display_entity_management_ui(
        repository=item_repo,
        entity_name_singular="Item",
        entity_name_plural="Itens",
        columns_to_display=item_cols_to_display,
        column_config=item_column_config,
        search_columns=["name", "desc", "code", "notes"],
        custom_search_label="Buscar Itens (por nome, descrição, código, observações):",
        editable_columns=["name", "desc", "code", "quantity", "unit", "notes"],
        # bidding_id is required for an item, but it's set by the parent selection, not direct edit here
        required_fields=["name", "quantity", "unit", "bidding_id"],
        # No fields_to_remove_before_update needed specifically for bidding_id as it's not editable.
        foreign_key_selection_configs=[fk_bidding_selection_config],
        # Default load_and_prepare_data in generic_entity_management will handle filtering by selected bidding_id.
        editor_key_suffix="items",
        is_editable=False,  # Set to read-only
    )
