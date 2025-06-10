import streamlit as st
import pandas as pd
from decimal import Decimal  # Not directly used here but often useful with Bidding
from db.models import BiddingMode  # Required for mode handling
from ..components.entity_manager import display_entity_management_ui
# from db.repositories import BiddingRepository # For type hinting


def prepare_biddings_dataframe_hook(df_raw: pd.DataFrame, selected_fks: dict = None):
    """
    Prepares the Biddings DataFrame for display:
    - Converts 'mode' enum to displayable string 'mode_display'.
    - Ensures 'date' is datetime (already handled by generic load_and_prepare).
    Args:
        df_raw (pd.DataFrame): The raw DataFrame loaded by load_and_prepare_data.
        selected_fks (dict, optional): Selected foreign keys, not used in this specific hook.
    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    if df_raw.empty:
        return df_raw

    df = df_raw.copy()  # Work with a copy

    # Create 'mode_display' from 'mode'
    if "mode" in df.columns:
        df["mode_display"] = df["mode"].apply(
            lambda x: x.value if isinstance(x, BiddingMode) else x
        )
    else:
        df["mode_display"] = None  # Ensure the column exists even if 'mode' doesn't

    # 'date' column is assumed to be converted to datetime by load_and_prepare_data.
    # If specific formatting or timezone handling for display were needed beyond what
    # DatetimeColumn offers, it could be done here.
    # For example, ensuring it's naive if it became timezone-aware unexpectedly:
    # if "date" in df.columns and not df["date"].empty and pd.api.types.is_datetime64_any_dtype(df["date"]):
    #    if df["date"].dt.tz is not None:
    #        df["date"] = df["date"].dt.tz_localize(None)
    # else:
    #    df["date"] = None # Ensure column exists

    return df


def display_biddings_tab(bidding_repo):  # bidding_repo: BiddingRepository
    """Displays the content for the Biddings management tab."""

    # Columns specifically for user display in st.data_editor
    # IDs and timestamps are excluded here but handled by column_config for disabling
    bidding_cols_to_display = [
        "process_number",
        "city",
        "mode_display",
        "date",
        "description",
        "status",
    ]

    bidding_column_config = {
        "id": st.column_config.NumberColumn(
            "ID", disabled=True, help="ID único da licitação."
        ),
        "process_number": st.column_config.TextColumn(
            "Nº do Processo",
            required=True,
            help="Número oficial do processo licitatório.",
        ),
        "city": st.column_config.TextColumn(
            "Cidade", required=True, help="Cidade onde ocorre a licitação."
        ),
        "mode_display": st.column_config.SelectboxColumn(
            "Modalidade",
            options=[mode.value for mode in BiddingMode],
            required=True,
            help="Modalidade da licitação (ex: Pregão Eletrônico).",
        ),
        "date": st.column_config.DatetimeColumn(
            "Data",
            format="YYYY-MM-DD HH:mm:ss",
            required=True,
            help="Data e hora da licitação.",
        ),
        "description": st.column_config.TextColumn(
            "Descrição", help="Breve descrição do objeto da licitação (opcional)."
        ),
        "status": st.column_config.TextColumn(
            "Status",
            help="Status atual da licitação (ex: Aberta, Em Andamento, Concluída) (opcional).",
        ),
        "created_at": st.column_config.DatetimeColumn(
            "Criado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
        "updated_at": st.column_config.DatetimeColumn(
            "Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True
        ),
    }

    display_entity_management_ui(
        repository=bidding_repo,
        entity_name_singular="Licitação",
        entity_name_plural="Licitações",
        columns_to_display=bidding_cols_to_display,
        column_config=bidding_column_config,
        search_columns=[
            "process_number",
            "city",
            "mode_display",
            "status",
            "description",
        ],
        custom_search_label="Buscar Licitações (por nº processo, cidade, modalidade, status, descrição):",
        editable_columns=[
            "process_number",
            "city",
            "mode_display",
            "date",
            "description",
            "status",
        ],
        required_fields=[
            "process_number",
            "city",
            "mode",
            "date",
        ],  # actual model field 'mode'
        special_conversions={
            "mode_display": {
                "target_field": "mode",
                "conversion_func": lambda x: BiddingMode(x) if x else None,
            },
            # Assuming editor returns datetime object for 'date'. If string, add conversion:
            "date": {
                "target_field": "date",
                "conversion_func": lambda x: pd.to_datetime(
                    x, errors="coerce"
                ).tz_localize(None)
                if not isinstance(x, pd.Timestamp)
                else (x.tz_localize(None) if x.tzinfo else x),
            },
        },
        fields_to_remove_before_update=["mode_display"],
        custom_data_processing_hook=prepare_biddings_dataframe_hook,
        editor_key_suffix="biddings",
        is_editable=True,  # Biddings table is editable
        auto_save=True,  # Enable auto-save for Biddings table
    )
