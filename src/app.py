from decimal import Decimal
import streamlit as st
import pandas as pd

from db.models import (
    Bidding,
    Item,
    Supplier,
    Bidder, # Renamed from Competitor
    Quote,
    Bid,
)

from repository.sqlmodel import SQLModelRepository # Updated import for new location
# from services import core as core_services # No longer needed in app.py
from services.dataframes import get_quotes_dataframe, get_bids_dataframe
# from state import initialize_session_state # Will be defined in-file
from services.plotting import create_quotes_figure, create_bids_figure
from ui.utils import get_options_map
from ui.dialogs import (
    manage_bidding_dialog_wrapper,
    manage_item_dialog_wrapper,
    manage_supplier_dialog_wrapper,
    manage_bidder_dialog_wrapper, # Renamed import
    set_dialog_repositories,  # To pass repo instances
)
from ui.management_tables_page import show_management_tables_view # New import

# --- Application Setup (must be first Streamlit command) ---
APP_TITLE = "📊 Sistema Integrado de Licitações" # Define APP_TITLE before using it
st.set_page_config(layout="wide", page_title=APP_TITLE)

# --- Session State Initialization Function (moved from state.py) ---
def initialize_session_state():
    """Initializes all session state variables for the application."""

    # IDs Selecionados
    if "selected_bidding_id" not in st.session_state:
        st.session_state.selected_bidding_id = None
    if "selected_item_id" not in st.session_state:
        st.session_state.selected_item_id = None

    # Nomes para exibição
    if "selected_bidding_name_for_display" not in st.session_state:
        st.session_state.selected_bidding_name_for_display = None
    if "selected_item_name_for_display" not in st.session_state:
        st.session_state.selected_item_name_for_display = None

    # Estado para controlar abertura de diálogos e edição
    for dialog_type in ["bidding", "item", "supplier", "bidder"]: # competitor -> bidder
        if f"show_manage_{dialog_type}_dialog" not in st.session_state:
            st.session_state[f"show_manage_{dialog_type}_dialog"] = False
        if f"editing_{dialog_type}_id" not in st.session_state:
            st.session_state[f"editing_{dialog_type}_id"] = None
        if f"confirm_delete_{dialog_type}" not in st.session_state:
            st.session_state[f"confirm_delete_{dialog_type}"] = False

    if "parent_bidding_id_for_item_dialog" not in st.session_state:
        st.session_state.parent_bidding_id_for_item_dialog = None

    # Navigation
    if "current_view" not in st.session_state:
        st.session_state.current_view = "Main View"

# --- Helper function to manage dialog visibility ---
def _open_dialog_exclusively(dialog_type_to_open: str):
    """Ensures only one dialog is open at a time."""
    st.session_state.show_manage_bidding_dialog = False
    st.session_state.show_manage_item_dialog = False
    st.session_state.show_manage_supplier_dialog = False
    st.session_state.show_manage_bidder_dialog = False # Renamed from competitor

    if dialog_type_to_open == "bidding":
        st.session_state.show_manage_bidding_dialog = True
    elif dialog_type_to_open == "item":
        st.session_state.show_manage_item_dialog = True
    elif dialog_type_to_open == "supplier":
        st.session_state.show_manage_supplier_dialog = True
    elif dialog_type_to_open == "bidder": # Renamed from competitor
        st.session_state.show_manage_bidder_dialog = True


# --- Database Repository Instances ---
db_url = "sqlite:///data/bidtrack.db"  # Define the database URL

bidding_repo = SQLModelRepository(Bidding, db_url)
item_repo = SQLModelRepository(Item, db_url)
supplier_repo = SQLModelRepository(Supplier, db_url)
bidder_repo = SQLModelRepository(Bidder, db_url) # competitor_repo -> bidder_repo, Competitor -> Bidder
quote_repo = SQLModelRepository(Quote, db_url)
bid_repo = SQLModelRepository(Bid, db_url)

# --- Constants ---
DEFAULT_BIDDING_SELECT_MESSAGE = "Selecione ou Cadastre uma Licitação..."
DEFAULT_ITEM_SELECT_MESSAGE = "Selecione ou Cadastre um Item..."
DEFAULT_SUPPLIER_SELECT_MESSAGE = "Selecione ou Cadastre um Fornecedor..."
DEFAULT_COMPETITOR_SELECT_MESSAGE = "Selecione ou Cadastre um Licitante..." # Renamed text
APP_TITLE = "📊 Sistema Integrado de Licitações"

# --- Initialize Session State ---
initialize_session_state()

# --- Sidebar Navigation ---
st.sidebar.title("Navegação")
current_view = st.sidebar.radio(
    "Escolha uma visualização:",
    ["Main View", "Management Tables"],
    key="navigation_radio" # Add key for explicit state management
)
if current_view != st.session_state.current_view:
    st.session_state.current_view = current_view
    # st.rerun() # Re-run to update view if selection changes

# --- View Functions ---
def show_main_view():
    # --- Seleção de Licitação e Botão de Gerenciamento ---
    col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
    all_biddings = bidding_repo.get_all() # Direct repository call
    bidding_options_map, bidding_option_ids = get_options_map(
        data_list=all_biddings,
        extra_cols=["city", "process_number", "mode"], # Changed order
        default_message=DEFAULT_BIDDING_SELECT_MESSAGE,
    )

    with col_bid_select:
        selected_bidding_id_from_sb = st.selectbox(
            "Escolha uma Licitação:",
            options=bidding_option_ids,
            format_func=lambda x: bidding_options_map.get(
                x, DEFAULT_BIDDING_SELECT_MESSAGE
            ),
            index=bidding_option_ids.index(st.session_state.selected_bidding_id)
            if st.session_state.selected_bidding_id in bidding_option_ids
            else 0,
            key="sb_bidding_main",
        )
    with col_bid_manage_btn:
        if st.button(
            "➕ Gerenciar Licitações", key="btn_manage_bids_main", use_container_width=True
        ):
            st.session_state.editing_bidding_id = selected_bidding_id_from_sb
            _open_dialog_exclusively("bidding")

    if selected_bidding_id_from_sb != st.session_state.selected_bidding_id:
        st.session_state.selected_bidding_id = selected_bidding_id_from_sb
        st.session_state.selected_bidding_name_for_display = (
            bidding_options_map.get(selected_bidding_id_from_sb)
            if selected_bidding_id_from_sb is not None
            else None
        )
        st.session_state.selected_item_id = None
        st.session_state.selected_item_name_for_display = None
        # Não é necessário st.rerun() aqui, o Streamlit reexecuta ao mudar o valor do selectbox

    if st.session_state.show_manage_bidding_dialog:
        is_open = manage_bidding_dialog_wrapper()
        if not is_open:
            st.session_state.show_manage_bidding_dialog = False

    # --- Seleção de Item e Botão de Gerenciamento ---
    items_for_select = [] # Initialize items_for_select here
    if st.session_state.selected_bidding_id is not None:
        col_item_select, col_item_manage_btn = st.columns(
            [5, 2], vertical_alignment="bottom"
        )

        # Fetch all items and then filter in Python
        all_items_from_repo = item_repo.get_all()
        items_for_select = [item for item in all_items_from_repo if item.bidding_id == st.session_state.selected_bidding_id]
        item_options_map, item_option_ids = get_options_map(
            data_list=items_for_select,
            name_col="name",
            default_message=DEFAULT_ITEM_SELECT_MESSAGE,
        )

        with col_item_select:
            bidding_display_label = (
                st.session_state.selected_bidding_name_for_display
                if st.session_state.selected_bidding_name_for_display
                else "Licitação Selecionada"
            )
            selected_item_id_from_sb = st.selectbox(
                "Escolha um Item da Licitação:", # Changed to static text
                options=item_option_ids,
                format_func=lambda x: item_options_map.get(x, DEFAULT_ITEM_SELECT_MESSAGE),
                index=item_option_ids.index(st.session_state.selected_item_id)
                if st.session_state.selected_item_id in item_option_ids
                else 0,
                key="sb_item_main",
            )
        with col_item_manage_btn:
            if st.button(
                "➕ Gerenciar Itens", key="btn_manage_items_main", use_container_width=True
            ):
                st.session_state.parent_bidding_id_for_item_dialog = (
                    st.session_state.selected_bidding_id
                )
                st.session_state.editing_item_id = selected_item_id_from_sb
                _open_dialog_exclusively("item")

        if selected_item_id_from_sb != st.session_state.selected_item_id:
            st.session_state.selected_item_id = selected_item_id_from_sb
            st.session_state.selected_item_name_for_display = (
                item_options_map.get(selected_item_id_from_sb)
                if selected_item_id_from_sb is not None
                else None
            )
            # Não é necessário st.rerun() aqui

    if st.session_state.show_manage_item_dialog:
        if st.session_state.parent_bidding_id_for_item_dialog is not None:
            is_open = manage_item_dialog_wrapper()
            if not is_open:
                st.session_state.show_manage_item_dialog = False
        else:
            st.session_state.show_manage_item_dialog = False

    # --- Exibição de Informações do Item, Expanders, Tabelas e Gráficos ---
    if st.session_state.selected_item_id is not None:
        try:
            if items_for_select:  # Check if the list is not empty
                current_item_details_list = [
                    item
                    for item in items_for_select
                    if item.id == st.session_state.selected_item_id
                ]
                if current_item_details_list:
                    current_item_details = current_item_details_list[0]
                    st.subheader("Detalhes")
                    item_code_display = current_item_details.code if current_item_details.code else "N/A"
                    st.markdown(f"**Código:** {item_code_display}")
                    st.markdown(f"**Descrição:** {current_item_details.desc if current_item_details.desc else 'N/A'}")
                    st.markdown(
                        f"**Quantidade:** {current_item_details.quantity} {current_item_details.unit}"
                    )

                    st.subheader("Orçamentos e Lances")
                    expander_cols = st.columns(2)
                    with expander_cols[0]:
                        with st.expander(
                            "Novo Orçamento",
                            expanded=False,
                        ):
                            col_supp_select, col_supp_manage = st.columns(
                                [3, 2], vertical_alignment="bottom"
                            )
                            all_suppliers = supplier_repo.get_all()
                            supplier_options_map, supplier_option_ids = get_options_map(
                                data_list=all_suppliers,
                                default_message=DEFAULT_SUPPLIER_SELECT_MESSAGE,
                            )
                            with col_supp_select:
                                selected_supplier_id_quote = st.selectbox(
                                    "Fornecedor*:",
                                    options=supplier_option_ids,
                                    format_func=lambda x: supplier_options_map.get(
                                        x, DEFAULT_SUPPLIER_SELECT_MESSAGE
                                    ),
                                    key="sb_supplier_quote_exp",
                                )
                            with col_supp_manage:
                                if st.button(
                                    "👤 Ger. Fornecedores",
                                    key="btn_manage_suppliers_quote_exp",
                                    use_container_width=True,
                                ):
                                    st.session_state.editing_supplier_id = (
                                        selected_supplier_id_quote
                                    )
                                    _open_dialog_exclusively("supplier")
                            with st.form(key="new_quote_form"):
                                quote_price = st.number_input(
                                    "Preço do Orçamento (Custo do Produto)*",
                                    min_value=0.01,
                                    format="%.2f",
                                    key="quote_price_input_exp",
                                )
                                quote_freight = st.number_input(
                                    "Frete (R$)",
                                    min_value=0.00,
                                    format="%.2f",
                                    key="quote_freight_input_exp",
                                    value=0.00
                                )
                                quote_additional_costs = st.number_input(
                                    "Custos Adicionais (R$)",
                                    min_value=0.00,
                                    format="%.2f",
                                    key="quote_additional_costs_input_exp",
                                    value=0.00
                                )
                                quote_taxes = st.number_input(
                                    "Impostos (%)",
                                    min_value=0.00,
                                    format="%.2f",
                                    key="quote_taxes_input_exp",
                                    help="Percentual de impostos sobre o preço de venda. Ex: 6 para 6%",
                                    value=0.00
                                )
                                quote_margin = st.number_input(
                                    "Margem de Lucro Desejada (%)*",
                                    min_value=0.0,
                                    format="%.2f",
                                    key="quote_margin_input_exp",
                                    help="Valor da margem em decimal. Ex: 0.2 para 20%",
                                )
                                quote_notes = st.text_area(
                                    "Notas do Orçamento", key="quote_notes_input_exp"
                                )
                                if st.form_submit_button("💾 Salvar Orçamento"):
                                    if (
                                        selected_supplier_id_quote
                                        and quote_price > 0
                                        and st.session_state.selected_item_id is not None
                                    ):
                                        try:
                                            new_quote_instance = Quote(
                                                item_id=st.session_state.selected_item_id, 
                                                supplier_id=selected_supplier_id_quote, 
                                                price=Decimal(str(quote_price)),
                                                freight=Decimal(str(quote_freight)),
                                                additional_costs=Decimal(str(quote_additional_costs)),
                                                taxes=Decimal(str(quote_taxes)),
                                                margin=Decimal(str(quote_margin)),
                                                notes=quote_notes if quote_notes else None,
                                            )
                                            added_quote = quote_repo.add(new_quote_instance)
                                            st.success(
                                                f"Orçamento de {supplier_options_map.get(selected_supplier_id_quote, 'Fornecedor')} (ID: {added_quote.id}) adicionado!"
                                            )
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao salvar orçamento: {e}")
                                    else:
                                        st.error(
                                            "Selecione um item, um fornecedor, e insira preço e margem válidos."
                                        )
                    with expander_cols[1]:
                        with st.expander(
                            "Novo Lance",
                            expanded=False,
                        ):
                            col_bidder_select, col_bidder_manage = st.columns(
                                [3, 2], vertical_alignment="bottom"
                            )
                            all_bidders = bidder_repo.get_all()
                            bidder_options_map, bidder_option_ids = get_options_map(
                                data_list=all_bidders,
                                default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE,
                            )

                            NO_BIDDER_SENTINEL = "___NO_BIDDER___"
                            initial_prompt_id = bidder_option_ids[0] if bidder_option_ids and bidder_option_ids[0] is None else "___NO_DEFAULT_PROMPT___"

                            bidder_options_map_display = bidder_options_map.copy()
                            bidder_option_ids_display = list(bidder_option_ids)
                            bidder_options_map_display[NO_BIDDER_SENTINEL] = "Nenhum Licitante"
                            
                            prompt_is_none_and_present = initial_prompt_id is None and None in bidder_option_ids_display
                            insert_idx = 1 if prompt_is_none_and_present else 0
                            if NO_BIDDER_SENTINEL not in bidder_option_ids_display:
                                 bidder_option_ids_display.insert(insert_idx, NO_BIDDER_SENTINEL)
                            
                            try:
                                default_bidder_index = bidder_option_ids_display.index(NO_BIDDER_SENTINEL)
                            except ValueError:
                                default_bidder_index = 0

                            with col_bidder_select: 
                                selected_bidder_id_bid = st.selectbox( 
                                    "Licitante:", 
                                    options=bidder_option_ids_display, 
                                    format_func=lambda x: bidder_options_map_display.get( 
                                        x, DEFAULT_COMPETITOR_SELECT_MESSAGE
                                    ),
                                    key="sb_bidder_bid_exp",
                                    index=default_bidder_index
                                )
                            with col_bidder_manage: 
                                if st.button(
                                    "👤 Ger. Licitantes",
                                    key="btn_manage_bidders_bid_exp",
                                    use_container_width=True,
                                ):
                                    st.session_state.editing_bidder_id = selected_bidder_id_bid
                                    _open_dialog_exclusively("bidder")
                            with st.form(key="new_bid_form"):
                                bid_price = st.number_input(
                                    "Preço do Lance*",
                                    min_value=0.01,
                                    format="%.2f",
                                    key="bid_price_input_exp",
                                )
                                bid_notes = st.text_area(
                                    "Notas do Lance", key="bid_notes_input_exp"
                                )
                                if st.form_submit_button("💾 Salvar Lance"):
                                    actual_bidder_id_to_save = selected_bidder_id_bid
                                    if selected_bidder_id_bid == NO_BIDDER_SENTINEL:
                                        actual_bidder_id_to_save = None
                                    
                                    if selected_bidder_id_bid is None:
                                        st.error("Por favor, selecione um Licitante ou a opção 'Nenhum Licitante'.")
                                    elif bid_price > 0 and st.session_state.selected_item_id is not None and hasattr(current_item_details, "bidding_id"):
                                        try:
                                            new_bid_instance = Bid(
                                                item_id=st.session_state.selected_item_id,
                                                bidding_id=current_item_details.bidding_id,
                                                bidder_id=actual_bidder_id_to_save,
                                                price=Decimal(str(bid_price)),
                                                notes=bid_notes if bid_notes else None,
                                            )
                                            added_bid = bid_repo.add(new_bid_instance)
                                            
                                            bidder_name_for_success_message = "Nenhum Licitante"
                                            if actual_bidder_id_to_save is not None:
                                                bidder_name_for_success_message = bidder_options_map_display.get(actual_bidder_id_to_save, 'Licitante Desconhecido')
                                            
                                            st.success(
                                                f"Lance de {bidder_name_for_success_message} (ID: {added_bid.id}) adicionado!"
                                            )
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao salvar lance: {e}")
                                    else:
                                        st.error(
                                            "Insira um preço de lance válido e certifique-se que um item está selecionado. Verifique também a seleção do licitante."
                                        )

                    all_quotes_from_repo = quote_repo.get_all()
                    quotes_for_item_list = [q for q in all_quotes_from_repo if q.item_id == st.session_state.selected_item_id]
                    all_bids_from_repo = bid_repo.get_all()
                    bids_for_item_list = [b for b in all_bids_from_repo if b.item_id == st.session_state.selected_item_id]

                    # Ensure all_items_list is available for get_quotes_dataframe
                    all_items_list = item_repo.get_all() # Fetch all items
                    quotes_for_item_list = [q for q in all_quotes_from_repo if q.item_id == st.session_state.selected_item_id]
                    all_bids_from_repo = bid_repo.get_all()
                    bids_for_item_list = [b for b in all_bids_from_repo if b.item_id == st.session_state.selected_item_id]

                    # Ensure all_items_list is available for get_quotes_dataframe
                    all_items_list = item_repo.get_all() # Fetch all items

                    # Prepare original DataFrames for comparison later
                    original_quotes_df = get_quotes_dataframe(
                        quotes_list=quotes_for_item_list,
                        suppliers_list=all_suppliers,
                        items_list=all_items_list
                    )
                    original_bids_df = get_bids_dataframe(
                        bids_list=bids_for_item_list,
                        bidders_list=all_bidders,
                        items_list=all_items_list
                    )

                    # --- Callback functions for data editor changes ---
                    def save_quotes_changes():
                        """Saves changes made to the quotes data editor, handling additions, updates, and deletions."""
                        st.write("DEBUG: Entering save_quotes_changes")
                        raw_editor_data = st.session_state.get('quotes_editor_main_view')
                        st.write("DEBUG: raw_editor_data from session_state:", raw_editor_data)
                        # st.write("DEBUG: original_quotes_df (snapshot before editor call):", original_quotes_df) # Avoid if huge
                        st.write("DEBUG: Type of original_quotes_df:", type(original_quotes_df))
                        if isinstance(original_quotes_df, pd.DataFrame):
                            st.write("DEBUG: original_quotes_df shape:", original_quotes_df.shape)
                            st.write("DEBUG: original_quotes_df IDs (head):", original_quotes_df['id'].head().tolist() if 'id' in original_quotes_df.columns else "No 'id' column in original_quotes_df")

                        changes_made = False
                        editable_quote_cols = ['price', 'freight', 'additional_costs', 'taxes', 'margin', 'notes']

                        # 1. Data Preparation
                        # raw_editor_data already fetched for debugging
                        current_editor_df = None
                        if isinstance(raw_editor_data, pd.DataFrame):
                            current_editor_df = raw_editor_data
                        elif isinstance(raw_editor_data, list):
                            try:
                                current_editor_df = pd.DataFrame(raw_editor_data)
                            except Exception: # Broad exception for conversion issues
                                current_editor_df = pd.DataFrame()
                        else:
                            current_editor_df = pd.DataFrame() # Handles None, dict, etc.

                        st.write("DEBUG: current_editor_df type:", type(current_editor_df))
                        if isinstance(current_editor_df, pd.DataFrame):
                            st.write("DEBUG: current_editor_df shape:", current_editor_df.shape)
                            st.write("DEBUG: current_editor_df IDs (head):", current_editor_df['id'].head().tolist() if 'id' in current_editor_df.columns else "No 'id' column in current_editor_df")
                            st.write("DEBUG: current_editor_df data (head):", current_editor_df.head())
                        else:
                            st.write("DEBUG: current_editor_df is not a DataFrame.")

                        # Use original_quotes_df as the baseline from when the editor was loaded
                        original_df_for_comparison = original_quotes_df

                        # Ensure 'id' columns are present and of a consistent type for comparison
                        original_ids = set()
                        if isinstance(original_df_for_comparison, pd.DataFrame) and 'id' in original_df_for_comparison.columns:
                            original_ids = set(original_df_for_comparison['id'].dropna().astype(str))
                        else: # original_df_for_comparison might not be a DataFrame if no items were loaded
                            st.warning("DEBUG: original_df_for_comparison is not a DataFrame or lacks 'id' column.")
                            # No return here, as original_ids will be empty, and logic should proceed (e.g. if current_editor_df has new rows)
                        st.write("DEBUG: original_ids set:", original_ids)

                        current_ids = set()
                        if isinstance(current_editor_df, pd.DataFrame) and 'id' in current_editor_df.columns:
                            current_ids = set(current_editor_df['id'].dropna().astype(str))
                        st.write("DEBUG: current_ids set:", current_ids)

                        # 3. Identify Changes
                        # DELETIONS
                        ids_to_delete = original_ids - current_ids
                        st.write("DEBUG: ids_to_delete set:", ids_to_delete)

                        if ids_to_delete: # Only proceed if there's something to delete
                            # SAFETY CHECK:
                            if not current_ids and isinstance(raw_editor_data, dict) and raw_editor_data:
                                st.error("ERRO CRÍTICO PREVENIDO: Tentativa de exclusão em massa devido a estado inesperado do editor (raw_editor_data é dict não vazio, resultando em current_ids vazio). Nenhuma alteração foi salva. Por favor, recarregue e verifique os dados.")
                                st.stop()
                                return

                            st.write(f"DEBUG: Proceeding with deleting IDs: {ids_to_delete}")
                            for quote_id_str in ids_to_delete:
                                try:
                                    quote_id_to_delete = int(quote_id_str) # Assuming quote IDs are integers
                                    quote_repo.delete(quote_id_to_delete)
                                    changes_made = True
                                    st.success(f"Orçamento ID {quote_id_to_delete} removido com sucesso.")
                                except ValueError:
                                    st.error(f"ID inválido para remoção: {quote_id_str}.")
                                except Exception as e:
                                st.error(f"Erro ao remover orçamento ID {quote_id_str}: {e}")

                        # ADDITIONS and UPDATES
                        for index, edited_row in current_editor_df.iterrows():
                            edited_row_id_original = edited_row.get('id') # Could be NaN, None, or a value
                            edited_row_id_str = str(edited_row_id_original) if pd.notna(edited_row_id_original) else ""

                            if pd.isna(edited_row_id_original) or not edited_row_id_str or edited_row_id_str not in original_ids:
                                # ADDITION attempt
                                # As supplier_id is missing, additions via this table are not supported.
                                # Only show a warning if the row seems to contain some data, not for completely empty new rows.
                                if not edited_row.drop('id', errors='ignore').isnull().all(): # Check if other fields have data
                                    st.warning(
                                        f"Adicionar novos orçamentos diretamente na tabela não é suportado devido à ausência de seleção de fornecedor. "
                                        f"Use o formulário 'Novo Orçamento'. Linha ignorada: {edited_row.to_dict()}"
                                    )
                            else:
                                # UPDATE
                                # Find the original row using the string version of ID for robust comparison
                                original_row_series_df = original_df_for_comparison[original_df_for_comparison['id'].astype(str) == edited_row_id_str]
                                if original_row_series_df.empty:
                                    st.error(f"Erro crítico: ID {edited_row_id_str} do editor não encontrado no original para atualização.")
                                    continue
                                original_row = original_row_series_df.iloc[0]

                                update_dict = {}
                                for col in editable_quote_cols:
                                    original_value = original_row[col]
                                    edited_value = edited_row[col]

                                    if col in ["price", "freight", "additional_costs", "taxes", "margin"]:
                                        try:
                                            # Convert original to Decimal, carefully handling None
                                            if original_value is None or (isinstance(original_value, str) and not original_value.strip()):
                                                original_decimal = None
                                            else:
                                                original_decimal = Decimal(str(original_value))

                                            # Convert edited to Decimal, carefully handling None and empty strings
                                            if edited_value is None or (isinstance(edited_value, str) and not str(edited_value).strip()):
                                                edited_decimal = None
                                            else:
                                                edited_decimal = Decimal(str(edited_value))

                                            # Compare, allowing for None == None
                                            if original_decimal != edited_decimal:
                                                update_dict[col] = edited_decimal # Store as Decimal
                                        except ValueError:
                                            st.error(f"Valor inválido para campo decimal {col} no orçamento ID {edited_row_id_str}: '{edited_value}'. Alteração ignorada.")
                                        except Exception as e: # Other conversion errors
                                            st.error(f"Erro ao processar campo {col} no orçamento ID {edited_row_id_str}: {e}. Alteração ignorada.")

                                    elif original_value != edited_value: # For non-decimal fields like 'notes'
                                        # Ensure NaN from editor (if field cleared) becomes None for DB
                                        update_dict[col] = None if pd.isna(edited_value) else edited_value

                                if update_dict:
                                    try:
                                        # Ensure ID is int for the repository
                                        quote_id_to_update = int(edited_row_id_str)
                                        quote_repo.update(quote_id_to_update, update_dict)
                                        changes_made = True
                                        st.success(f"Orçamento ID {quote_id_to_update} atualizado com sucesso.")
                                    except ValueError:
                                        st.error(f"ID inválido para atualização: {edited_row_id_str}.")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar orçamento ID {edited_row_id_str}: {e}. Dados: {update_dict}")

                        if changes_made:
                            st.rerun()

                    def save_bids_changes():
                        """Saves changes made to the bids data editor, handling additions, updates, and deletions."""
                        st.write("DEBUG: Entering save_bids_changes")
                        raw_editor_data_bids = st.session_state.get('bids_editor_main_view')
                        st.write("DEBUG: raw_editor_data_bids from session_state:", raw_editor_data_bids)
                        st.write("DEBUG: Type of original_bids_df:", type(original_bids_df))
                        if isinstance(original_bids_df, pd.DataFrame):
                            st.write("DEBUG: original_bids_df shape:", original_bids_df.shape)
                            st.write("DEBUG: original_bids_df IDs (head):", original_bids_df['id'].head().tolist() if 'id' in original_bids_df.columns else "No 'id' column in original_bids_df")

                        changes_made = False
                        editable_bid_cols = ['price', 'notes']

                        # 1. Data Preparation
                        # raw_editor_data_bids already fetched for debugging
                        current_editor_df = None
                        if isinstance(raw_editor_data_bids, pd.DataFrame):
                            current_editor_df = raw_editor_data_bids
                        elif isinstance(raw_editor_data_bids, list):
                            try:
                                current_editor_df = pd.DataFrame(raw_editor_data_bids)
                            except Exception: # Broad exception for conversion issues
                                current_editor_df = pd.DataFrame()
                        else:
                            current_editor_df = pd.DataFrame() # Handles None, dict, etc.

                        st.write("DEBUG: current_editor_df (bids) type:", type(current_editor_df))
                        if isinstance(current_editor_df, pd.DataFrame):
                            st.write("DEBUG: current_editor_df (bids) shape:", current_editor_df.shape)
                            st.write("DEBUG: current_editor_df (bids) IDs (head):", current_editor_df['id'].head().tolist() if 'id' in current_editor_df.columns else "No 'id' column in current_editor_df (bids)")
                            st.write("DEBUG: current_editor_df (bids) data (head):", current_editor_df.head())
                        else:
                            st.write("DEBUG: current_editor_df (bids) is not a DataFrame.")

                        original_df_for_comparison = original_bids_df # Baseline from editor load

                        # Ensure 'id' columns are present and of a consistent type for comparison
                        original_ids = set()
                        if isinstance(original_df_for_comparison, pd.DataFrame) and 'id' in original_df_for_comparison.columns:
                            original_ids = set(original_df_for_comparison['id'].dropna().astype(str))
                        else:
                            st.warning("DEBUG: original_df_for_comparison (bids) is not a DataFrame or lacks 'id' column.")
                        st.write("DEBUG: original_ids_bids set:", original_ids)

                        current_ids = set()
                        if isinstance(current_editor_df, pd.DataFrame) and 'id' in current_editor_df.columns:
                            current_ids = set(current_editor_df['id'].dropna().astype(str))
                        st.write("DEBUG: current_ids_bids set:", current_ids)

                        # 3. Identify Changes
                        # DELETIONS
                        ids_to_delete = original_ids - current_ids
                        st.write("DEBUG: ids_to_delete_bids set:", ids_to_delete)

                        if ids_to_delete: # Only proceed if there's something to delete
                            # SAFETY CHECK for bids:
                            if not current_ids and isinstance(raw_editor_data_bids, dict) and raw_editor_data_bids:
                                st.error("ERRO CRÍTICO PREVENIDO (LANCES): Tentativa de exclusão em massa devido a estado inesperado do editor. Nenhuma alteração foi salva. Por favor, recarregue.")
                                st.stop()
                                return

                            st.write(f"DEBUG: Proceeding with deleting bid IDs: {ids_to_delete}")
                            for bid_id_str in ids_to_delete:
                                try:
                                    bid_id_to_delete = int(bid_id_str) # Assuming bid IDs are integers
                                    bid_repo.delete(bid_id_to_delete)
                                changes_made = True
                                st.success(f"Lance ID {bid_id_to_delete} removido com sucesso.")
                            except ValueError:
                                st.error(f"ID inválido para remoção de lance: {bid_id_str}.")
                            except Exception as e:
                                st.error(f"Erro ao remover lance ID {bid_id_str}: {e}")

                        # ADDITIONS and UPDATES
                        for index, edited_row in current_editor_df.iterrows():
                            edited_row_id_original = edited_row.get('id')
                            edited_row_id_str = str(edited_row_id_original) if pd.notna(edited_row_id_original) else ""

                            if pd.isna(edited_row_id_original) or not edited_row_id_str or edited_row_id_str not in original_ids:
                                # ADDITION attempt
                                if not edited_row.drop('id', errors='ignore').isnull().all():
                                    st.warning(
                                        f"Adicionar novos lances diretamente na tabela não é suportado devido à ausência de seleção de licitante. "
                                        f"Use o formulário 'Novo Lance'. Linha ignorada: {edited_row.to_dict()}"
                                    )
                            else:
                                # UPDATE
                                original_row_series_df = original_df_for_comparison[original_df_for_comparison['id'].astype(str) == edited_row_id_str]
                                if original_row_series_df.empty:
                                    st.error(f"Erro crítico: ID de lance {edited_row_id_str} do editor não encontrado no original para atualização.")
                                    continue
                                original_row = original_row_series_df.iloc[0]

                                update_dict = {}
                                for col in editable_bid_cols:
                                    original_value = original_row[col]
                                    edited_value = edited_row[col]

                                    if col == "price":
                                        try:
                                            if edited_value is None or (isinstance(edited_value, str) and not str(edited_value).strip()):
                                                # Price is required for bids, throw error if empty
                                                st.error(f"Preço não pode ser vazio para o lance ID {edited_row_id_str}. Alteração ignorada.")
                                                update_dict.clear() # Prevent partial update for this row
                                                break # Stop processing this row's columns

                                            original_decimal = Decimal(str(original_value)) if original_value is not None else None
                                            edited_decimal = Decimal(str(edited_value)) # Price cannot be None here

                                            if original_decimal != edited_decimal:
                                                update_dict[col] = edited_decimal
                                        except ValueError:
                                            st.error(f"Valor inválido para preço no lance ID {edited_row_id_str}: '{edited_value}'. Alteração ignorada.")
                                            update_dict.clear()
                                            break
                                        except Exception as e:
                                            st.error(f"Erro ao processar preço no lance ID {edited_row_id_str}: {e}. Alteração ignorada.")
                                            update_dict.clear()
                                            break
                                    elif col == "notes": # For 'notes'
                                        if original_value != edited_value:
                                            update_dict[col] = None if pd.isna(edited_value) else edited_value

                                if update_dict: # Check if any valid changes were collected for this row
                                    try:
                                        bid_id_to_update = int(edited_row_id_str)
                                        bid_repo.update(bid_id_to_update, update_dict)
                                        changes_made = True
                                        st.success(f"Lance ID {bid_id_to_update} atualizado com sucesso.")
                                    except ValueError:
                                        st.error(f"ID inválido para atualização de lance: {edited_row_id_str}.")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar lance ID {edited_row_id_str}: {e}. Dados: {update_dict}")

                        if changes_made:
                            st.rerun()

                    table_cols_display = st.columns(2)
                    with table_cols_display[0]:
                        st.markdown("##### Orçamentos do Item")
                        if not original_quotes_df.empty:
                            # original_quotes_df is the direct output of get_quotes_dataframe (all columns, 'id' is a column)

                            # 2. Update column_config_quotes_main
                            column_config_quotes_main = {
                                "id": None,  # Hide 'id' column by default
                                "item_id": None, # Hide 'item_id'
                                "supplier_id": None, # Hide 'supplier_id'
                                "created_at": None, # Hide 'created_at'
                                "updated_at": None, # Hide 'updated_at'

                                "item_name": None, # Hide "Item" column by default
                                "supplier_name": st.column_config.TextColumn("Fornecedor", disabled=True, help="Nome do fornecedor (não editável aqui)"),
                                "price": st.column_config.NumberColumn("Custo Base (R$)", format="%.2f", required=True, help="Preço de custo do produto/serviço junto ao fornecedor."),
                                "freight": st.column_config.NumberColumn("Frete (R$)", format="%.2f", help="Valor do frete."),
                                "additional_costs": st.column_config.NumberColumn("Custos Adic. (R$)", format="%.2f", help="Outros custos diretos."),
                                "taxes": st.column_config.NumberColumn("Impostos (%)", format="%.2f", help="Percentual de impostos incidentes sobre o preço de venda. Ex: 6 para 6%."),
                                "margin": st.column_config.NumberColumn("Margem (%)", format="%.2f", required=True, help="Margem de lucro desejada sobre o custo total. Ex: 20 para 20%."),
                                "calculated_price": st.column_config.NumberColumn("Preço Final Calculado", format="R$ %.2f", disabled=True, help="Preço final de venda (calculado automaticamente)."),
                                "notes": st.column_config.TextColumn("Notas", help="Observações sobre o orçamento."),
                            }
                            # Ensure all columns from original_quotes_df are present in config, adding None if missing
                            for col_name in original_quotes_df.columns:
                                if col_name not in column_config_quotes_main:
                                    column_config_quotes_main[col_name] = None # Hide unspecified columns by default

                            # 1. DataFrame for Editor: Pass original_quotes_df
                            # hide_index=True means edited_quotes_df will have a range index. 'id' will be a column in edited_quotes_df.
                            edited_quotes_df = st.data_editor(
                                original_quotes_df, # Pass the full original DataFrame
                                column_config=column_config_quotes_main,
                                key="quotes_editor_main_view",
                                use_container_width=True,
                                hide_index=True,
                                num_rows="dynamic",
                                on_change=save_quotes_changes # Use the new callback
                            )
                            # The save button is no longer needed here as on_change handles it.
                        else:
                            st.info("Nenhum orçamento cadastrado para este item.")

                    with table_cols_display[1]:
                        st.markdown("##### Lances do Item")
                        if not original_bids_df.empty:
                            # original_bids_df is the direct output of get_bids_dataframe (all columns, 'id' is a column)

                            # 2. Update column_config_bids_main
                            column_config_bids_main = {
                                "id": None, # Hide 'id' column by default
                                "item_id": None, # Hide 'item_id'
                                "bidding_id": None, # Hide 'bidding_id'
                                "bidder_id": None, # Hide 'bidder_id'
                                "created_at": None, # Hide 'created_at'
                                "updated_at": None, # Hide 'updated_at'

                                "item_name": None, # Hide "Item" column by default
                                "bidder_name": st.column_config.TextColumn("Licitante", disabled=True, help="Nome do licitante (não editável aqui)."),
                                "price": st.column_config.NumberColumn("Preço Ofertado (R$)", format="R$ %.2f", min_value=0.01, required=True, help="Valor do lance ofertado."),
                                "notes": st.column_config.TextColumn("Notas", help="Observações sobre o lance."),
                            }
                            # Ensure all columns from original_bids_df are present in config, adding None if missing
                            for col_name in original_bids_df.columns:
                                if col_name not in column_config_bids_main:
                                    column_config_bids_main[col_name] = None # Hide unspecified columns by default

                            # 1. DataFrame for Editor: Pass original_bids_df
                            # hide_index=True means edited_bids_df will have a range index. 'id' will be a column in edited_bids_df.
                            edited_bids_df = st.data_editor(
                                original_bids_df, # Pass the full original DataFrame
                                column_config=column_config_bids_main,
                                key="bids_editor_main_view",
                                use_container_width=True,
                                hide_index=True,
                                num_rows="dynamic",
                                on_change=save_bids_changes # Use the new callback
                            )
                            # The save button is no longer needed here as on_change handles it.
                        else:
                            st.info("Nenhum lance cadastrado para este item.")

                    st.subheader("Gráficos")
                    graph_cols_display = st.columns(2)
                    with graph_cols_display[0]:
                        # Revised logic for quotes_df_for_graph
                        quotes_data_from_session = st.session_state.get("quotes_editor_main_view")
                        temp_quotes_df = None

                        if isinstance(quotes_data_from_session, pd.DataFrame):
                            temp_quotes_df = quotes_data_from_session
                        elif isinstance(quotes_data_from_session, list):
                            try: # Attempt to convert list of dicts
                                temp_quotes_df = pd.DataFrame(quotes_data_from_session)
                            except Exception: # If conversion fails, treat as invalid
                                temp_quotes_df = None

                        original_is_valid_df = isinstance(original_quotes_df, pd.DataFrame)

                        if temp_quotes_df is not None and not temp_quotes_df.empty:
                            quotes_df_for_graph = temp_quotes_df
                        elif original_is_valid_df and not original_quotes_df.empty:
                            quotes_df_for_graph = original_quotes_df
                        elif original_is_valid_df: # Original is DataFrame but might be empty
                            quotes_df_for_graph = original_quotes_df
                        else: # Fallback if original is also not a valid df
                            quotes_df_for_graph = pd.DataFrame()

                        if (
                            not quotes_df_for_graph.empty
                            and "calculated_price" in quotes_df_for_graph.columns
                            and "supplier_name" in quotes_df_for_graph.columns
                        ):
                            st.plotly_chart(
                                create_quotes_figure(quotes_df_for_graph),
                                use_container_width=True,
                            )
                        else:
                            st.caption("Gráfico de orçamentos não disponível.")
                    with graph_cols_display[1]:
                        # Revised logic for bids_df_for_graph
                        bids_data_from_session = st.session_state.get("bids_editor_main_view")
                        temp_bids_df = None

                        if isinstance(bids_data_from_session, pd.DataFrame):
                            temp_bids_df = bids_data_from_session
                        elif isinstance(bids_data_from_session, list):
                            try: # Attempt to convert list of dicts
                                temp_bids_df = pd.DataFrame(bids_data_from_session)
                            except Exception: # If conversion fails, treat as invalid
                                temp_bids_df = None

                        original_bids_is_valid_df = isinstance(original_bids_df, pd.DataFrame)

                        if temp_bids_df is not None and not temp_bids_df.empty:
                            bids_df_for_graph = temp_bids_df
                        elif original_bids_is_valid_df and not original_bids_df.empty:
                            bids_df_for_graph = original_bids_df
                        elif original_bids_is_valid_df: # Original is DataFrame but might be empty
                            bids_df_for_graph = original_bids_df
                        else: # Fallback if original is also not a valid df
                            bids_df_for_graph = pd.DataFrame()

                        if (
                            not bids_df_for_graph.empty # This check is now safer
                            and "price" in bids_df_for_graph.columns
                            and "bidder_name" in bids_df_for_graph.columns
                            # 'created_at' is on original_bids_df, if bids_df_for_graph is from session_state it might not have it
                            # For consistency and if 'created_at' is essential for the bid figure, consider always using original_bids_df
                            # or ensuring 'created_at' is preserved/added to the session state version.
                            # For now, we'll assume 'created_at' is primarily for sorting/display which original_bids_df handles.
                            # If create_bids_figure strictly needs 'created_at' from its input df, this logic might need adjustment.
                            # Let's use original_bids_df for create_bids_figure to ensure 'created_at' is present.
                        ):
                            min_quote_price_val = (
                                quotes_df_for_graph["calculated_price"].min()
                                if not quotes_df_for_graph.empty
                                and "calculated_price" in quotes_df_for_graph.columns
                                else None
                            )
                            st.plotly_chart(
                                create_bids_figure(
                                    original_bids_df, min_quote_price_val # Using original_bids_df to ensure 'created_at'
                                ),
                                use_container_width=True,
                            )
                        else:
                            st.caption("Gráfico de lances não disponível.")
                else:
                    if st.session_state.selected_item_id is not None:
                        st.warning(
                            "Item selecionado não é válido para a licitação atual ou foi removido."
                        )
        except IndexError:
            st.warning("Ocorreu um erro ao tentar exibir os detalhes do item.")
            if st.session_state.selected_item_id is not None:
                st.session_state.selected_item_id = None
                st.session_state.selected_item_name_for_display = None

    # Abrir diálogos de gerenciamento de Fornecedores/Concorrentes se flags estiverem ativas
    # These dialogs are often triggered by buttons within the expanders above.
    if st.session_state.get("show_manage_supplier_dialog", False):
        is_open = manage_supplier_dialog_wrapper()
        if not is_open:
            st.session_state.show_manage_supplier_dialog = False
    if st.session_state.get("show_manage_bidder_dialog", False):
        is_open = manage_bidder_dialog_wrapper()
        if not is_open:
            st.session_state.show_manage_bidder_dialog = False

# Initialize dialog repositories
# This needs to be called once after repositories are initialized.
# Explicitly type hint repository variables for clarity
bidding_repo: SQLModelRepository[Bidding] = bidding_repo
item_repo: SQLModelRepository[Item] = item_repo
supplier_repo: SQLModelRepository[Supplier] = supplier_repo
bidder_repo: SQLModelRepository[Bidder] = bidder_repo # competitor_repo -> bidder_repo, Competitor -> Bidder
quote_repo: SQLModelRepository[Quote] = quote_repo
bid_repo: SQLModelRepository[Bid] = bid_repo

set_dialog_repositories(
    b_repo=bidding_repo,
    i_repo=item_repo,
    s_repo=supplier_repo,
    bd_repo=bidder_repo, # c_repo -> bd_repo
    q_repo=quote_repo,
    bi_repo=bid_repo,
)

# --- Application Title (can be set after page config) ---
st.title(APP_TITLE)

# --- Conditional View Rendering ---
if st.session_state.current_view == "Main View":
    show_main_view()
elif st.session_state.current_view == "Management Tables":
    show_management_tables_view(bidding_repo, item_repo, supplier_repo, quote_repo, bidder_repo, bid_repo)
