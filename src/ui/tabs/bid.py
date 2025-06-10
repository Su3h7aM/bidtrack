import streamlit as st
import pandas as pd
from decimal import Decimal  # Keep for column config if needed
from ..components.entity_manager import display_entity_management_ui
from services.dataframes import get_bids_dataframe  # Corrected import

# Type hinting for repositories (optional but good practice)
# from db.repositories import BidRepository, BiddingRepository, ItemRepository, BidderRepository


def prepare_bids_dataframe_via_service(
    bid_repo,  # : BidRepository,
    selected_fks: dict,
    item_repo,  # : ItemRepository,
    bidder_repo,  # : BidderRepository
) -> pd.DataFrame:
    """
    Prepares the Bids DataFrame by:
    1. Filtering raw bid data based on the selected bidding_id.
    2. Calling the centralized get_bids_dataframe service function.
    """
    bidding_id = selected_fks.get("bidding_id")
    if bidding_id is None:
        return pd.DataFrame()  # Return empty if no bidding selected

    # 1. Fetch all bids and filter them by bidding_id
    all_bids_list_models = bid_repo.get_all()  # List of Bid model instances
    if not all_bids_list_models:
        return pd.DataFrame()

    # Filter bids that belong to the selected bidding
    # Assuming Bid model has a 'bidding_id' attribute
    filtered_bids_models = [
        bid for bid in all_bids_list_models if bid.bidding_id == bidding_id
    ]

    if not filtered_bids_models:
        return pd.DataFrame()  # No bids for the selected bidding

    # 2. Fetch all items and bidders (needed by get_bids_dataframe for mapping)
    all_items_list_models = item_repo.get_all()
    all_bidders_list_models = bidder_repo.get_all()

    # 3. Call the service function to get the processed DataFrame
    # The service function now handles item_name, bidder_name, and date conversions.
    bids_display_df = get_bids_dataframe(
        bids_list=filtered_bids_models,
        bidders_list=all_bidders_list_models if all_bidders_list_models else [],
        items_list=all_items_list_models if all_items_list_models else [],
    )

    return bids_display_df


def display_bids_tab(bid_repo, bidding_repo, item_repo, bidder_repo):
    """Displays the content for the Bids management tab."""

    fk_bidding_selection_config = {
        "label": "Escolha uma Licitação para ver seus Lances",
        "repository_for_options": bidding_repo,
        "options_map_config": {
            "name_col": "process_number",  # Assumes Bidding model has 'process_number'
            "extra_cols": ["city", "process_number", "mode"],
            "default_message": "Selecione uma Licitação...",
        },
        "filter_column_on_df": "bidding_id",
        "block_if_parent_not_selected": True,
    }

    # These columns are now expected to be delivered by get_bids_dataframe
    # User-facing display columns in the editor:
    bid_cols_to_display = ["item_name", "bidder_name", "price", "notes"]

    bid_column_config = {
        "id": st.column_config.NumberColumn("ID Lance", disabled=True),
        "item_name": st.column_config.TextColumn("Item", disabled=True),
        "bidder_name": st.column_config.TextColumn("Licitante", disabled=True),
        "price": st.column_config.NumberColumn(
            "Preço Ofertado",
            format="R$ %.2f",
            min_value=0.01,
            required=True,
            help="Valor do lance ofertado.",
        ),
        "notes": st.column_config.TextColumn(
            "Notas do Lance", help="Observações sobre o lance (opcional)."
        ),
        "item_id": st.column_config.NumberColumn("ID Item (Ref)", disabled=True),
        "bidding_id": st.column_config.NumberColumn(
            "ID Licitação (Ref)", disabled=True
        ),
        "bidder_id": st.column_config.NumberColumn("ID Licitante (Ref)", disabled=True),
        "created_at": st.column_config.DatetimeColumn(
            "Criado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
        "updated_at": st.column_config.DatetimeColumn(
            "Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
    }

    display_entity_management_ui(
        repository=bid_repo,
        entity_name_singular="Lance",
        entity_name_plural="Lances",
        columns_to_display=bid_cols_to_display,
        column_config=bid_column_config,
        search_columns=["item_name", "bidder_name", "notes"],
        custom_search_label="Buscar Lances (por item, licitante, notas):",
        editable_columns=["price", "notes"],
        required_fields=["price", "item_id", "bidding_id"],
        decimal_fields=["price"],  # Still needed for handle_save_changes
        fields_to_remove_before_update=["item_name", "bidder_name"],
        foreign_key_selection_configs=[fk_bidding_selection_config],
        custom_dataframe_preparation_func=lambda main_repo,
        fks_dict: prepare_bids_dataframe_via_service(
            main_repo, fks_dict, item_repo, bidder_repo
        ),
        editor_key_suffix="bids",
        is_editable=False,  # Set to read-only
    )
