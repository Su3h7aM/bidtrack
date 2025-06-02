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

# --- Página Principal da Aplicação ---
st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
all_biddings = bidding_repo.get_all() # Direct repository call
bidding_options_map, bidding_option_ids = get_options_map(
    data_list=all_biddings,
    extra_cols=["process_number", "city", "mode"],
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
        st.rerun() # Add rerun for immediate effect

# --- Seleção de Item e Botão de Gerenciamento ---
items_for_select = []
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
            f"Escolha um Item da Licitação '{bidding_display_label}':",
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
            st.rerun() # Add rerun
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
                st.markdown(
                    f"**Item Selecionado:** {current_item_details.name} (ID: {st.session_state.selected_item_id})"
                )
                st.markdown(f"**Descrição:** {current_item_details.desc}")
                st.markdown(
                    f"**Quantidade:** {current_item_details.quantity} {current_item_details.unit}"
                )
                st.markdown("---")

                expander_cols = st.columns(2)
                with expander_cols[0]:
                    with st.expander(
                        f"➕ Adicionar Novo Orçamento para {current_item_details.name}",
                        expanded=False,
                    ):
                        col_supp_select, col_supp_manage = st.columns(
                            [3, 2], vertical_alignment="bottom"
                        )
                        all_suppliers = supplier_repo.get_all() # Direct repository call
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
                                "Preço do Orçamento (Custo do Produto)*", # Clarified label
                                min_value=0.01,
                                format="%.2f",
                                key="quote_price_input_exp",
                            )
                            quote_freight = st.number_input( # New field
                                "Frete (R$)",
                                min_value=0.00,
                                format="%.2f",
                                key="quote_freight_input_exp",
                                value=0.00 # Default value
                            )
                            quote_additional_costs = st.number_input( # New field
                                "Custos Adicionais (R$)",
                                min_value=0.00,
                                format="%.2f",
                                key="quote_additional_costs_input_exp",
                                value=0.00 # Default value
                            )
                            quote_taxes = st.number_input( # New field
                                "Impostos (%)",
                                min_value=0.00,
                                format="%.2f",
                                key="quote_taxes_input_exp",
                                help="Percentual de impostos sobre o preço de venda. Ex: 6 para 6%",
                                value=0.00 # Default value
                            )
                            quote_margin = st.number_input(
                                "Margem de Lucro Desejada (%)*", # Clarified label and type
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
                                            item_id=st.session_state.selected_item_id, # type: ignore
                                            supplier_id=selected_supplier_id_quote, # type: ignore
                                            price=Decimal(str(quote_price)), # Custo do Produto
                                            freight=Decimal(str(quote_freight)), # New
                                            additional_costs=Decimal(str(quote_additional_costs)), # New
                                            taxes=Decimal(str(quote_taxes)), # New
                                            margin=Decimal(str(quote_margin)), # Will be used if calculation is client-side prior to saving, or stored as is. The issue implies margin is a target for the formula.
                                            notes=quote_notes if quote_notes else None,
                                        )
                                        added_quote = quote_repo.add(new_quote_instance) # Direct repository call
                                        st.success(
                                            f"Orçamento de {supplier_options_map.get(selected_supplier_id_quote, 'Fornecedor')} (ID: {added_quote.id}) adicionado!"
                                        )
                                        # Clear form or reset relevant session state if needed here
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar orçamento: {e}")
                                else:
                                    st.error(
                                        "Selecione um item, um fornecedor, e insira preço e margem válidos."
                                    )
                with expander_cols[1]:
                    with st.expander(
                        f"➕ Adicionar Novo Lance para {current_item_details.name}",
                        expanded=False,
                    ):
                        col_bidder_select, col_bidder_manage = st.columns( # Renamed variables
                            [3, 2], vertical_alignment="bottom"
                        )
                        all_bidders = bidder_repo.get_all()
                        bidder_options_map, bidder_option_ids = get_options_map(
                            data_list=all_bidders,
                            default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE, # This is "Selecione ou Cadastre um Licitante..."
                        )

                        NO_BIDDER_SENTINEL = "___NO_BIDDER___"
                        initial_prompt_id = bidder_option_ids[0] if bidder_option_ids and bidder_option_ids[0] is None else "___NO_DEFAULT_PROMPT___"


                        bidder_options_map_display = bidder_options_map.copy()
                        bidder_option_ids_display = list(bidder_option_ids)

                        bidder_options_map_display[NO_BIDDER_SENTINEL] = "Nenhum Licitante" # Changed text
                        
                        # Insert "Nenhum Licitante" after the initial "Selecione..." prompt if it exists
                        # initial_prompt_id is bidder_option_ids[0] if it's None, otherwise a sentinel not equal to None
                        prompt_is_none_and_present = initial_prompt_id is None and None in bidder_option_ids_display
                        
                        if prompt_is_none_and_present:
                            insert_idx = 1 # Insert after the "Selecione..."
                        else: # No "Selecione..." prompt (or it's not None), or list was empty. Add "Nenhum" at the start.
                            insert_idx = 0
                        
                        # Ensure not to insert if NO_BIDDER_SENTINEL is already there (e.g. from a previous run if list is not rebuilt)
                        if NO_BIDDER_SENTINEL not in bidder_option_ids_display:
                             bidder_option_ids_display.insert(insert_idx, NO_BIDDER_SENTINEL)
                        
                        # Determine the index for the default selection ("Nenhum Licitante")
                        try:
                            default_bidder_index = bidder_option_ids_display.index(NO_BIDDER_SENTINEL)
                        except ValueError:
                            default_bidder_index = 0 # Fallback, though should not happen if inserted

                        with col_bidder_select: 
                            selected_bidder_id_bid = st.selectbox( 
                                "Licitante:", 
                                options=bidder_option_ids_display, 
                                format_func=lambda x: bidder_options_map_display.get( 
                                    x, DEFAULT_COMPETITOR_SELECT_MESSAGE # This is "Selecione ou Cadastre um Licitante..."
                                ),
                                key="sb_bidder_bid_exp",
                                index=default_bidder_index # Set "Nenhum Licitante" as default
                            )
                        with col_bidder_manage: 
                            if st.button(
                                "👤 Ger. Licitantes", # Renamed text
                                key="btn_manage_bidders_bid_exp", # Renamed key
                                use_container_width=True,
                            ):
                                st.session_state.editing_bidder_id = ( # Renamed variable
                                    selected_bidder_id_bid # Renamed variable
                                )
                                _open_dialog_exclusively("bidder") # Renamed variable
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
                                
                                # Validation: User must select a Licitante or "Nenhum Licitante".
                                # The initial prompt (e.g., "Selecione...") should not be submittable as a valid choice.
                                # initial_prompt_id was defined based on bidder_option_ids[0] being None.
                                # If the selectbox is defaulted to "Nenhum Licitante", this check might change.
                                # The important thing is that `selected_bidder_id_bid` should not be the ID of the prompt message.
                                # The prompt message (e.g. "Selecione...") has ID `None` if `get_options_map` adds it.
                                if selected_bidder_id_bid is None: # This means the "Selecione..." prompt is selected
                                    st.error("Por favor, selecione um Licitante ou a opção 'Nenhum Licitante'.")
                                elif bid_price > 0 and st.session_state.selected_item_id is not None and hasattr(current_item_details, "bidding_id"):
                                    try:
                                        new_bid_instance = Bid(
                                            item_id=st.session_state.selected_item_id,
                                            bidding_id=current_item_details.bidding_id,
                                            bidder_id=actual_bidder_id_to_save, # Use processed ID (can be None)
                                            price=Decimal(str(bid_price)),
                                            notes=bid_notes if bid_notes else None,
                                        )
                                        added_bid = bid_repo.add(new_bid_instance)
                                        
                                        bidder_name_for_success_message = "Nenhum Licitante" # Default if actual_bidder_id_to_save is None
                                        if actual_bidder_id_to_save is not None:
                                            bidder_name_for_success_message = bidder_options_map_display.get(actual_bidder_id_to_save, 'Licitante Desconhecido')
                                        
                                        st.success(
                                            f"Lance de {bidder_name_for_success_message} (ID: {added_bid.id}) adicionado!"
                                        )
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar lance: {e}")
                                else:
                                    # This error covers cases like bid_price <= 0 or item not selected,
                                    # or if the "Selecione..." prompt was somehow submitted (though caught above).
                                    st.error(
                                        "Insira um preço de lance válido e certifique-se que um item está selecionado. Verifique também a seleção do licitante."
                                    )

                # Fetch all quotes and bids, then filter in Python for the selected item
                all_quotes_from_repo = quote_repo.get_all()
                quotes_for_item_list = [q for q in all_quotes_from_repo if q.item_id == st.session_state.selected_item_id]

                all_bids_from_repo = bid_repo.get_all()
                bids_for_item_list = [b for b in all_bids_from_repo if b.item_id == st.session_state.selected_item_id]

                # Note: all_suppliers and all_bidders are already fetched above in the expanders using direct repo calls.

                quotes_for_item_df_display = get_quotes_dataframe(
                    quotes_for_item_list, all_suppliers
                )
                bids_for_item_df_display = get_bids_dataframe(
                    bids_for_item_list, all_bidders # Renamed variable
                )

                table_cols_display = st.columns(2)
                with table_cols_display[0]:
                    st.markdown("##### Orçamentos Recebidos")
                    if not quotes_for_item_df_display.empty:
                        # Columns to display, matching those returned by get_quotes_dataframe
                        display_cols_quotes = [ # English internal names for selection
                            "supplier_name", 
                            "price", 
                            "freight", 
                            "additional_costs",
                            "taxes", 
                            "margin", 
                            "calculated_price", 
                            "notes",
                        ]
                        # Filter for existing columns to prevent KeyErrors if some are missing
                        # This list (final_display_cols_quotes) will contain English names
                        final_display_cols_quotes = [
                            col
                            for col in display_cols_quotes
                            if col in quotes_for_item_df_display.columns 
                        ]
                        # Keys are English internal names, labels are Portuguese for UI
                        column_config_quotes = {
                            "supplier_name": st.column_config.TextColumn(label="Nome do Fornecedor"),
                            "price": st.column_config.NumberColumn(label="Preço Base", format="R$ %.2f"),
                            "freight": st.column_config.NumberColumn(label="Frete", format="R$ %.2f"),
                            "additional_costs": st.column_config.NumberColumn(label="Custos Adicionais", format="R$ %.2f"),
                            "taxes": st.column_config.NumberColumn(label="Impostos (%)", format="%.2f%%"),
                            "margin": st.column_config.NumberColumn(label="Margem (%)", format="%.2f%%"),
                            "calculated_price": st.column_config.NumberColumn(label="Preço Calculado", format="R$ %.2f"),
                            "notes": st.column_config.TextColumn(label="Notas"),
                            # Date columns (created_at, update_at) are intentionally omitted from display_cols_quotes
                        }
                        st.dataframe(
                            quotes_for_item_df_display[final_display_cols_quotes], # df has English cols, final_display_cols_quotes has English cols
                            hide_index=True,
                            use_container_width=True,
                            column_config=column_config_quotes,
                        )
                    else:
                        st.info("Nenhum orçamento cadastrado para este item.")
                with table_cols_display[1]:
                    st.markdown("##### Lances Recebidos")
                    if not bids_for_item_df_display.empty:
                        # Columns to display, matching those returned by get_bids_dataframe
                        display_cols_bids = [ # English internal names for selection
                            "bidder_name", 
                            "price",
                            "notes",
                        ]
                        # Filter for existing columns
                        # This list (final_display_cols_bids) will contain English names
                        final_display_cols_bids = [
                            col
                            for col in display_cols_bids
                            if col in bids_for_item_df_display.columns
                        ]
                        # Keys are English internal names, labels are Portuguese for UI
                        column_config_bids = {
                            "bidder_name": st.column_config.TextColumn(label="Nome do Licitante"),
                            "price": st.column_config.NumberColumn(label="Preço Ofertado", format="R$ %.2f"),
                            "notes": st.column_config.TextColumn(label="Notas"),
                            # Date columns (created_at, update_at) are intentionally omitted from display_cols_bids
                        }
                        st.dataframe(
                            bids_for_item_df_display[final_display_cols_bids], # df has English cols, final_display_cols_bids has English cols
                            hide_index=True,
                            use_container_width=True,
                            column_config=column_config_bids,
                        )
                    else:
                        st.info("Nenhum lance cadastrado para este item.")

                st.markdown("---")
                st.subheader("Gráficos do Item")
                graph_cols_display = st.columns(2)
                with graph_cols_display[0]:
                    if (
                        not quotes_for_item_df_display.empty
                        # Checks now use English column names, as DataFrame has English columns
                        and "calculated_price" in quotes_for_item_df_display.columns 
                        and "supplier_name" in quotes_for_item_df_display.columns
                    ):
                        st.plotly_chart(
                            create_quotes_figure(quotes_for_item_df_display),
                            use_container_width=True,
                        )
                    else:
                        st.caption("Gráfico de orçamentos não disponível.")
                with graph_cols_display[1]:
                    if (
                        not bids_for_item_df_display.empty
                        # Checks now use English column names
                        and "price" in bids_for_item_df_display.columns
                        and "bidder_name" in bids_for_item_df_display.columns 
                    ):
                        min_quote_price_val = ( 
                            quotes_for_item_df_display["calculated_price"].min() # Use English name
                            if not quotes_for_item_df_display.empty
                            and "calculated_price" in quotes_for_item_df_display.columns # Use English name
                            else None
                        )
                        st.plotly_chart(
                            create_bids_figure(
                                bids_for_item_df_display, min_quote_price_val
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
                    # Não reseta aqui para permitir que o selectbox tente se corrigir no próximo rerun
    except IndexError:
        st.warning("Ocorreu um erro ao tentar exibir os detalhes do item.")
        if st.session_state.selected_item_id is not None:
            st.session_state.selected_item_id = None
            st.session_state.selected_item_name_for_display = None

# Abrir diálogos de gerenciamento de Fornecedores/Concorrentes se flags estiverem ativas
if st.session_state.get("show_manage_supplier_dialog", False):
    is_open = manage_supplier_dialog_wrapper()
    if not is_open:
        st.session_state.show_manage_supplier_dialog = False
        st.rerun() # Add rerun
if st.session_state.get("show_manage_bidder_dialog", False): # Renamed state variable
    is_open = manage_bidder_dialog_wrapper() # Renamed function call
    if not is_open:
        st.session_state.show_manage_bidder_dialog = False
        st.rerun() # Add rerun
