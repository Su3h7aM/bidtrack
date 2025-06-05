import streamlit as st
import pandas as pd
from decimal import Decimal # Keep for column config if needed, though calc is now in service
from ui.generic_entity_management import display_entity_management_ui
from services.dataframes import get_quotes_dataframe # Corrected import

# Type hinting for repositories (optional but good practice)
# from db.repositories import QuoteRepository, BiddingRepository, ItemRepository, SupplierRepository

def prepare_quotes_dataframe_via_service(
    quote_repo, # : QuoteRepository,
    selected_fks: dict,
    item_repo,    # : ItemRepository,
    supplier_repo # : SupplierRepository
) -> pd.DataFrame:
    """
    Prepares the Quotes DataFrame by:
    1. Filtering raw quote data based on the selected bidding_id.
    2. Calling the centralized get_quotes_dataframe service function.
    """
    bidding_id = selected_fks.get("bidding_id")
    if bidding_id is None:
        # The generic UI will show "select parent" message based on block_if_parent_not_selected
        return pd.DataFrame() # Return empty if no bidding selected

    # 1. Fetch all items to filter by bidding_id and later pass for name mapping
    all_items_list = item_repo.get_all()
    if not all_items_list:
        return pd.DataFrame()

    items_df = pd.DataFrame([item.model_dump() for item in all_items_list])
    if items_df.empty or 'bidding_id' not in items_df.columns or 'id' not in items_df.columns:
        return pd.DataFrame()

    items_for_selected_bidding = items_df[items_df["bidding_id"] == bidding_id]
    if items_for_selected_bidding.empty:
        return pd.DataFrame() # No items for this bidding, so no quotes to show

    item_ids_for_selected_bidding = set(items_for_selected_bidding["id"])

    # 2. Fetch all quotes and filter them
    all_quotes_list_models = quote_repo.get_all() # List of Quote model instances
    if not all_quotes_list_models:
        return pd.DataFrame()

    # Filter quotes that belong to the items of the selected bidding
    filtered_quotes_models = [
        quote for quote in all_quotes_list_models if quote.item_id in item_ids_for_selected_bidding
    ]

    if not filtered_quotes_models:
        return pd.DataFrame() # No quotes for the items in the selected bidding

    # 3. Fetch all suppliers (needed by get_quotes_dataframe for mapping)
    all_suppliers_list_models = supplier_repo.get_all()
    # all_items_list_models is already all_items_list

    # 4. Call the service function to get the processed DataFrame
    # The service function now handles item_name, supplier_name, calculated_price, and date conversions.
    quotes_display_df = get_quotes_dataframe(
        quotes_list=filtered_quotes_models,
        suppliers_list=all_suppliers_list_models if all_suppliers_list_models else [],
        items_list=all_items_list # Pass all items; service will map based on IDs in filtered_quotes_models
    )

    return quotes_display_df

def display_quotes_tab(quote_repo, bidding_repo, item_repo, supplier_repo):
    """Displays the content for the Quotes management tab."""

    fk_bidding_selection_config = {
        "label": "Escolha uma Licitação para ver seus Orçamentos",
        "repository_for_options": bidding_repo,
        "options_map_config": {
            "name_col": "process_number", # Assumes Bidding model has 'process_number'
            "extra_cols": ["city", "process_number", "mode"],
            "default_message": "Selecione uma Licitação...",
        },
        "filter_column_on_df": "bidding_id",
        "block_if_parent_not_selected": True
    }

    # These columns are now expected to be delivered by get_quotes_dataframe
    # User-facing display columns in the editor:
    quote_cols_to_display = [
        "item_name", "supplier_name", "price", "freight", "additional_costs",
        "taxes", "margin", "calculated_price", "notes"
    ]

    quote_column_config = {
        "id": st.column_config.NumberColumn("ID Orçamento", disabled=True),
        "item_name": st.column_config.TextColumn("Item", disabled=True),
        "supplier_name": st.column_config.TextColumn("Fornecedor", disabled=True),
        "price": st.column_config.NumberColumn("Preço Base (Custo)", format="R$ %.2f", required=True, help="Custo base do produto/serviço junto ao fornecedor."),
        "freight": st.column_config.NumberColumn("Frete (R$)", format="R$ %.2f", help="Custo do frete (opcional)."),
        "additional_costs": st.column_config.NumberColumn("Custos Adic. (R$)", format="R$ %.2f", help="Outros custos adicionais (opcional)."),
        "taxes": st.column_config.NumberColumn("Impostos (%)", format="%.2f", help="Percentual de impostos sobre o preço + frete + custos (ex: 6 para 6%)."),
        "margin": st.column_config.NumberColumn("Margem (%)", format="%.2f", required=True, help="Margem de lucro desejada sobre o preço com impostos (ex: 20 para 20%)."),
        "calculated_price": st.column_config.NumberColumn("Preço Final Calculado", format="R$ %.2f", disabled=True, help="Preço final do orçamento para o cliente."),
        "notes": st.column_config.TextColumn("Notas", help="Observações adicionais sobre o orçamento (opcional)."),
        "item_id": st.column_config.NumberColumn("ID Item (Ref)", disabled=True),
        "supplier_id": st.column_config.NumberColumn("ID Fornecedor (Ref)", disabled=True),
        # Dates are now datetime objects from service, Streamlit will format them.
        "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
        "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
    }

    display_entity_management_ui(
        repository=quote_repo,
        entity_name_singular="Orçamento",
        entity_name_plural="Orçamentos",
        columns_to_display=quote_cols_to_display,
        column_config=quote_column_config,
        search_columns=["item_name", "supplier_name", "notes"],
        custom_search_label="Buscar Orçamentos (por item, fornecedor, notas):",
        editable_columns=["price", "freight", "additional_costs", "taxes", "margin", "notes"],
        required_fields=["price", "margin", "item_id", "supplier_id"],
        decimal_fields=["price", "freight", "additional_costs", "taxes", "margin"], # Still needed for handle_save_changes
        fields_to_remove_before_update=['item_name', 'supplier_name', 'calculated_price'], # These are display-only
        foreign_key_selection_configs=[fk_bidding_selection_config],
        custom_dataframe_preparation_func=lambda main_repo, fks_dict: prepare_quotes_dataframe_via_service(main_repo, fks_dict, item_repo, supplier_repo),
        editor_key_suffix="quotes",
        is_editable=False # Set to read-only
    )
