import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time

from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid, BiddingMode # Added BiddingMode as it's used by Bidding
from repository import SQLModelRepository

# --- Database Repository Instances ---
db_url = "sqlite:///data/bidtrack.db" # Define the database URL

bidding_repo = SQLModelRepository(Bidding, db_url)
item_repo = SQLModelRepository(Item, db_url)
supplier_repo = SQLModelRepository(Supplier, db_url)
competitor_repo = SQLModelRepository(Competitor, db_url)
quote_repo = SQLModelRepository(Quote, db_url)
bid_repo = SQLModelRepository(Bid, db_url)

# --- Initialize Session State ---
from state import initialize_session_state
initialize_session_state()

# --- Imports from UI module ---
from ui.constants import (
    DEFAULT_BIDDING_SELECT_MESSAGE,
    DEFAULT_ITEM_SELECT_MESSAGE,
    DEFAULT_SUPPLIER_SELECT_MESSAGE,
    DEFAULT_COMPETITOR_SELECT_MESSAGE,
    APP_TITLE
)
from ui.plotting import create_quotes_figure, create_bids_figure
from ui.utils import get_options_map
from ui.dialogs import (
    manage_bidding_dialog_wrapper,
    manage_item_dialog_wrapper,
    manage_supplier_dialog_wrapper,
    manage_competitor_dialog_wrapper,
    set_dialog_repositories # To pass repo instances
)

# Initialize dialog repositories
# This needs to be called once after repositories are initialized.
set_dialog_repositories(
    b_repo=bidding_repo, i_repo=item_repo,
    s_repo=supplier_repo, c_repo=competitor_repo,
    q_repo=quote_repo, bi_repo=bid_repo
)

# --- Página Principal da Aplicação ---
st.set_page_config(layout="wide", page_title=APP_TITLE) # APP_TITLE is now imported
st.title(APP_TITLE) # APP_TITLE is now imported

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
all_biddings = bidding_repo.get_all()
if all_biddings is None: all_biddings = []
# get_options_map and DEFAULT_BIDDING_SELECT_MESSAGE are now imported
bidding_options_map, bidding_option_ids = get_options_map(data_list=all_biddings, extra_cols=['process_number', 'city', 'mode'], default_message=DEFAULT_BIDDING_SELECT_MESSAGE)

with col_bid_select:
    selected_bidding_id_from_sb = st.selectbox("Escolha uma Licitação:",
                                               options=bidding_option_ids,
                                               format_func=lambda x: bidding_options_map.get(x, DEFAULT_BIDDING_SELECT_MESSAGE), # Imported constant
                                               index=bidding_option_ids.index(st.session_state.selected_bidding_id) if st.session_state.selected_bidding_id in bidding_option_ids else 0,
                                               key="sb_bidding_main")
with col_bid_manage_btn:
    if st.button("➕ Gerenciar Licitações", key="btn_manage_bids_main", use_container_width=True):
        st.session_state.editing_bidding_id = selected_bidding_id_from_sb 
        st.session_state.show_manage_bidding_dialog = True

if selected_bidding_id_from_sb != st.session_state.selected_bidding_id:
    st.session_state.selected_bidding_id = selected_bidding_id_from_sb
    st.session_state.selected_bidding_name_for_display = bidding_options_map.get(selected_bidding_id_from_sb) if selected_bidding_id_from_sb is not None else None
    st.session_state.selected_item_id = None 
    st.session_state.selected_item_name_for_display = None
    # Não é necessário st.rerun() aqui, o Streamlit reexecuta ao mudar o valor do selectbox

if st.session_state.show_manage_bidding_dialog: manage_bidding_dialog_wrapper() # Imported function

# --- Seleção de Item e Botão de Gerenciamento ---
items_for_select = []
if st.session_state.selected_bidding_id is not None:
    col_item_select, col_item_manage_btn = st.columns([5, 2], vertical_alignment="bottom")

    all_items = item_repo.get_all()
    if all_items is None: all_items = []
    items_for_select = [item for item in all_items if item.bidding_id == st.session_state.selected_bidding_id]
    # get_options_map and DEFAULT_ITEM_SELECT_MESSAGE are now imported
    item_options_map, item_option_ids = get_options_map(data_list=items_for_select, name_col='name', default_message=DEFAULT_ITEM_SELECT_MESSAGE)

    with col_item_select:
        bidding_display_label = st.session_state.selected_bidding_name_for_display if st.session_state.selected_bidding_name_for_display else "Licitação Selecionada"
        selected_item_id_from_sb = st.selectbox(f"Escolha um Item da Licitação '{bidding_display_label}':",
                                                options=item_option_ids,
                                                format_func=lambda x: item_options_map.get(x, DEFAULT_ITEM_SELECT_MESSAGE), # Imported constant
                                                index=item_option_ids.index(st.session_state.selected_item_id) if st.session_state.selected_item_id in item_option_ids else 0,
                                                key="sb_item_main")
    with col_item_manage_btn:
        if st.button("➕ Gerenciar Itens", key="btn_manage_items_main", use_container_width=True):
            st.session_state.parent_bidding_id_for_item_dialog = st.session_state.selected_bidding_id
            st.session_state.editing_item_id = selected_item_id_from_sb 
            st.session_state.show_manage_item_dialog = True

    if selected_item_id_from_sb != st.session_state.selected_item_id:
        st.session_state.selected_item_id = selected_item_id_from_sb
        st.session_state.selected_item_name_for_display = item_options_map.get(selected_item_id_from_sb) if selected_item_id_from_sb is not None else None
        # Não é necessário st.rerun() aqui

if st.session_state.show_manage_item_dialog:
    if st.session_state.parent_bidding_id_for_item_dialog is not None: manage_item_dialog_wrapper() # Imported function
    else: st.session_state.show_manage_item_dialog = False

# --- Exibição de Informações do Item, Expanders, Tabelas e Gráficos ---
if st.session_state.selected_item_id is not None:
    try:
        if items_for_select: # Check if the list is not empty
            current_item_details_list = [item for item in items_for_select if item.id == st.session_state.selected_item_id]
            if current_item_details_list:
                current_item_details = current_item_details_list[0]
                st.markdown(f"**Item Selecionado:** {current_item_details.name} (ID: {st.session_state.selected_item_id})")
                st.markdown(f"**Descrição:** {current_item_details.desc}")
                st.markdown(f"**Quantidade:** {current_item_details.quantity} {current_item_details.unit}")
                st.markdown("---")

                expander_cols = st.columns(2)
                with expander_cols[0]:
                    with st.expander(f"➕ Adicionar Novo Orçamento para {current_item_details.name}", expanded=False):
                        col_supp_select, col_supp_manage = st.columns([3,2], vertical_alignment="bottom")
                        all_suppliers = supplier_repo.get_all()
                        if all_suppliers is None: all_suppliers = []
                        # get_options_map and DEFAULT_SUPPLIER_SELECT_MESSAGE are now imported
                        supplier_options_map, supplier_option_ids = get_options_map(data_list=all_suppliers, default_message=DEFAULT_SUPPLIER_SELECT_MESSAGE)
                        with col_supp_select:
                            selected_supplier_id_quote = st.selectbox("Fornecedor*:", options=supplier_option_ids, format_func=lambda x: supplier_options_map.get(x, DEFAULT_SUPPLIER_SELECT_MESSAGE), key="sb_supplier_quote_exp") # Imported constant
                        with col_supp_manage:
                            if st.button("👤 Ger. Fornecedores", key="btn_manage_suppliers_quote_exp", use_container_width=True):
                                st.session_state.editing_supplier_id = selected_supplier_id_quote
                                st.session_state.show_manage_supplier_dialog = True
                        with st.form(key="new_quote_form"):
                            quote_price = st.number_input("Preço do Orçamento*", min_value=0.01, format="%.2f", key="quote_price_input_exp")
                            quote_margin = st.number_input("Margem*", min_value=0.0, format="%.2f", key="quote_margin_input_exp", help="Valor da margem em decimal. Ex: 0.2 para 20%")
                            quote_notes = st.text_area("Notas do Orçamento", key="quote_notes_input_exp")
                            if st.form_submit_button("💾 Salvar Orçamento"):
                                if selected_supplier_id_quote and quote_price > 0 and st.session_state.selected_item_id is not None:
                                    try:
                                        new_quote = Quote(
                                            item_id=st.session_state.selected_item_id,
                                            supplier_id=selected_supplier_id_quote,
                                            price=quote_price,
                                            margin=quote_margin, # Added margin
                                            notes=quote_notes
                                        )
                                        quote_repo.add(new_quote)
                                        st.success(f"Orçamento de {supplier_options_map.get(selected_supplier_id_quote, 'Fornecedor')} adicionado!"); st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar orçamento: {e}")
                                else: st.error("Selecione um item, um fornecedor e insira um preço válido.")
                with expander_cols[1]:
                    with st.expander(f"➕ Adicionar Novo Lance para {current_item_details.name}", expanded=False):
                        col_comp_select, col_comp_manage = st.columns([3,2], vertical_alignment="bottom")
                        all_competitors = competitor_repo.get_all()
                        if all_competitors is None: all_competitors = []
                        # get_options_map and DEFAULT_COMPETITOR_SELECT_MESSAGE are now imported
                        competitor_options_map, competitor_option_ids = get_options_map(data_list=all_competitors, default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE)
                        with col_comp_select:
                            selected_competitor_id_bid = st.selectbox("Concorrente*:", options=competitor_option_ids, format_func=lambda x: competitor_options_map.get(x, DEFAULT_COMPETITOR_SELECT_MESSAGE), key="sb_competitor_bid_exp") # Imported constant
                        with col_comp_manage:
                            if st.button("👤 Ger. Concorrentes", key="btn_manage_competitors_bid_exp", use_container_width=True):
                                st.session_state.editing_competitor_id = selected_competitor_id_bid
                                st.session_state.show_manage_competitor_dialog = True
                        with st.form(key="new_bid_form"):
                            bid_price = st.number_input("Preço do Lance*", min_value=0.01, format="%.2f", key="bid_price_input_exp")
                            bid_notes = st.text_area("Notas do Lance", key="bid_notes_input_exp")
                            if st.form_submit_button("💾 Salvar Lance"):
                                if selected_competitor_id_bid and bid_price > 0 and st.session_state.selected_item_id is not None and hasattr(current_item_details, 'bidding_id'):
                                    try:
                                        new_bid = Bid(
                                            item_id=st.session_state.selected_item_id,
                                            bidding_id=current_item_details.bidding_id, # Sourced from current_item_details
                                            competitor_id=selected_competitor_id_bid,
                                            price=bid_price,
                                            notes=bid_notes
                                        )
                                        bid_repo.add(new_bid)
                                        st.success(f"Lance de {competitor_options_map.get(selected_competitor_id_bid, 'Concorrente')} adicionado!"); st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar lance: {e}")
                                else: st.error("Selecione um item, um concorrente, certifique-se que o item tem `bidding_id` e insira um preço válido.")

                all_quotes = quote_repo.get_all()
                if all_quotes is None: all_quotes = []
                quotes_for_item_list = [q for q in all_quotes if q.item_id == st.session_state.selected_item_id]

                all_bids = bid_repo.get_all()
                if all_bids is None: all_bids = []
                bids_for_item_list = [b for b in all_bids if b.item_id == st.session_state.selected_item_id]

                # TODO: The merging logic with supplier/competitor names needs to be re-thought.
                # For now, let's prepare display data as list of dicts or adapt create_figure functions.
                # This will be addressed in a subsequent step.
                quotes_for_item_df_display = pd.DataFrame([q.model_dump() for q in quotes_for_item_list]) # Temporary
                bids_for_item_df_display = pd.DataFrame([b.model_dump() for b in bids_for_item_list]) # Temporary

                # TEMP: Add supplier/competitor names for display - this needs proper handling with relationships or dedicated DTOs
                if not quotes_for_item_df_display.empty and all_suppliers:
                    supplier_map = {s.id: s.name for s in all_suppliers}
                    quotes_for_item_df_display['supplier_name'] = quotes_for_item_df_display['supplier_id'].map(supplier_map)

                if not bids_for_item_df_display.empty and all_competitors:
                    competitor_map = {c.id: c.name for c in all_competitors}
                    bids_for_item_df_display['competitor_name'] = bids_for_item_df_display['competitor_id'].map(competitor_map)


                table_cols_display = st.columns(2) 
                with table_cols_display[0]:
                    st.markdown("##### Orçamentos Recebidos")
                    # Add formatting for date columns
                    if not quotes_for_item_df_display.empty: # Check if DataFrame is not empty before formatting
                        if 'created_at' in quotes_for_item_df_display.columns:
                            quotes_for_item_df_display['created_at'] = pd.to_datetime(quotes_for_item_df_display['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        if 'update_at' in quotes_for_item_df_display.columns and pd.notnull(quotes_for_item_df_display['update_at']).all():
                            quotes_for_item_df_display['update_at'] = pd.to_datetime(quotes_for_item_df_display['update_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

                    if not quotes_for_item_df_display.empty: st.dataframe(quotes_for_item_df_display[['supplier_name', 'price', 'created_at', 'update_at', 'notes']], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum orçamento cadastrado para este item.")
                with table_cols_display[1]:
                    st.markdown("##### Lances Recebidos")
                    if not bids_for_item_df_display.empty:
                        bids_to_show = bids_for_item_df_display.copy(); 
                        if 'created_at' in bids_to_show.columns: # Check for created_at now
                            bids_to_show['created_at'] = pd.to_datetime(bids_to_show['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        if 'update_at' in bids_to_show.columns and pd.notnull(bids_to_show['update_at']).all(): # ensure not all are NaT/None
                            bids_to_show['update_at'] = pd.to_datetime(bids_to_show['update_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        # The model has 'updated_at'. If 'update_at' is truly intended for display,
                        # it must be present in bids_to_show DataFrame.
                        # Let's assume 'update_at' is a specific column name in the DataFrame for display purposes.
                        st.dataframe(bids_to_show[['competitor_name', 'price', 'created_at', 'notes', 'update_at']], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum lance cadastrado para este item.")

                st.markdown("---"); st.subheader("Gráficos do Item")
                graph_cols_display = st.columns(2)
                with graph_cols_display[0]:
                    if not quotes_for_item_df_display.empty: st.plotly_chart(create_quotes_figure(quotes_for_item_df_display), use_container_width=True) # Imported function
                    else: st.caption("Gráfico de orçamentos não disponível.")
                with graph_cols_display[1]:
                    if not bids_for_item_df_display.empty and 'price' in bids_for_item_df_display.columns:
                        min_quote_price_val = quotes_for_item_df_display['price'].min() if not quotes_for_item_df_display.empty and 'price' in quotes_for_item_df_display.columns else None
                        st.plotly_chart(create_bids_figure(bids_for_item_df_display, min_quote_price_val), use_container_width=True) # Imported function
                    else: st.caption("Gráfico de lances não disponível.")
            else:
                if st.session_state.selected_item_id is not None:
                    st.warning("Item selecionado não é válido para a licitação atual ou foi removido.");
                    # Não reseta aqui para permitir que o selectbox tente se corrigir no próximo rerun
    except IndexError:
        st.warning("Ocorreu um erro ao tentar exibir os detalhes do item.")
        if st.session_state.selected_item_id is not None:
            st.session_state.selected_item_id = None; st.session_state.selected_item_name_for_display = None;

# Abrir diálogos de gerenciamento de Fornecedores/Concorrentes se flags estiverem ativas
if st.session_state.get('show_manage_supplier_dialog', False): manage_supplier_dialog_wrapper() # Imported function
if st.session_state.get('show_manage_competitor_dialog', False): manage_competitor_dialog_wrapper() # Imported function
