import streamlit as st
import pandas as pd

from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid # Added BiddingMode as it's used by Bidding
from repository import SQLModelRepository
from data_processing import get_quotes_dataframe, get_bids_dataframe

# --- Database Repository Instances ---
db_url = "sqlite:///data/bidtrack.db" # Define the database URL

bidding_repo = SQLModelRepository(Bidding, db_url)
item_repo = SQLModelRepository(Item, db_url)
supplier_repo = SQLModelRepository(Supplier, db_url)
competitor_repo = SQLModelRepository(Competitor, db_url)
quote_repo = SQLModelRepository(Quote, db_url)
bid_repo = SQLModelRepository(Bid, db_url)

# --- Constants ---
DEFAULT_BIDDING_SELECT_MESSAGE = "Selecione ou Cadastre uma Licitação..."
DEFAULT_ITEM_SELECT_MESSAGE = "Selecione ou Cadastre um Item..."
DEFAULT_SUPPLIER_SELECT_MESSAGE = "Selecione ou Cadastre um Fornecedor..."
DEFAULT_COMPETITOR_SELECT_MESSAGE = "Selecione ou Cadastre um Concorrente..."
APP_TITLE = "📊 Sistema Integrado de Licitações"

# --- Initialize Session State ---
from state import initialize_session_state
initialize_session_state()

# --- Imports from UI module ---
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
st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
all_biddings = bidding_repo.get_all()
if all_biddings is None: all_biddings = []
bidding_options_map, bidding_option_ids = get_options_map(data_list=all_biddings, extra_cols=['process_number', 'city', 'mode'], default_message=DEFAULT_BIDDING_SELECT_MESSAGE)

with col_bid_select:
    selected_bidding_id_from_sb = st.selectbox("Escolha uma Licitação:",
                                               options=bidding_option_ids,
                                               format_func=lambda x: bidding_options_map.get(x, DEFAULT_BIDDING_SELECT_MESSAGE),
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

if st.session_state.show_manage_bidding_dialog: manage_bidding_dialog_wrapper()

# --- Seleção de Item e Botão de Gerenciamento ---
items_for_select = []
if st.session_state.selected_bidding_id is not None:
    col_item_select, col_item_manage_btn = st.columns([5, 2], vertical_alignment="bottom")

    all_items = item_repo.get_all()
    if all_items is None: all_items = []
    items_for_select = [item for item in all_items if item.bidding_id == st.session_state.selected_bidding_id]
    item_options_map, item_option_ids = get_options_map(data_list=items_for_select, name_col='name', default_message=DEFAULT_ITEM_SELECT_MESSAGE)

    with col_item_select:
        bidding_display_label = st.session_state.selected_bidding_name_for_display if st.session_state.selected_bidding_name_for_display else "Licitação Selecionada"
        selected_item_id_from_sb = st.selectbox(f"Escolha um Item da Licitação '{bidding_display_label}':",
                                                options=item_option_ids,
                                                format_func=lambda x: item_options_map.get(x, DEFAULT_ITEM_SELECT_MESSAGE),
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
    if st.session_state.parent_bidding_id_for_item_dialog is not None: manage_item_dialog_wrapper()
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
                        supplier_options_map, supplier_option_ids = get_options_map(data_list=all_suppliers, default_message=DEFAULT_SUPPLIER_SELECT_MESSAGE)
                        with col_supp_select:
                            selected_supplier_id_quote = st.selectbox("Fornecedor*:", options=supplier_option_ids, format_func=lambda x: supplier_options_map.get(x, DEFAULT_SUPPLIER_SELECT_MESSAGE), key="sb_supplier_quote_exp")
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
                        competitor_options_map, competitor_option_ids = get_options_map(data_list=all_competitors, default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE)
                        with col_comp_select:
                            selected_competitor_id_bid = st.selectbox("Concorrente*:", options=competitor_option_ids, format_func=lambda x: competitor_options_map.get(x, DEFAULT_COMPETITOR_SELECT_MESSAGE), key="sb_competitor_bid_exp")
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

                # Use the new data processing functions
                all_suppliers = supplier_repo.get_all() # Ensure all_suppliers is defined
                if all_suppliers is None: all_suppliers = []
                all_competitors = competitor_repo.get_all() # Ensure all_competitors is defined
                if all_competitors is None: all_competitors = []

                quotes_for_item_df_display = get_quotes_dataframe(quotes_for_item_list, all_suppliers)
                bids_for_item_df_display = get_bids_dataframe(bids_for_item_list, all_competitors)

                table_cols_display = st.columns(2) 
                with table_cols_display[0]:
                    st.markdown("##### Orçamentos Recebidos")
                    if not quotes_for_item_df_display.empty:
                        # Columns to display, matching those returned by get_quotes_dataframe
                        display_cols_quotes = ['supplier_name', 'price', 'margin', 'created_at', 'update_at', 'notes']
                        # Filter for existing columns to prevent KeyErrors if some are missing
                        final_display_cols_quotes = [col for col in display_cols_quotes if col in quotes_for_item_df_display.columns]
                        st.dataframe(quotes_for_item_df_display[final_display_cols_quotes], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum orçamento cadastrado para este item.")
                with table_cols_display[1]:
                    st.markdown("##### Lances Recebidos")
                    if not bids_for_item_df_display.empty:
                        # Columns to display, matching those returned by get_bids_dataframe
                        display_cols_bids = ['competitor_name', 'price', 'created_at', 'notes', 'update_at']
                        # Filter for existing columns
                        final_display_cols_bids = [col for col in display_cols_bids if col in bids_for_item_df_display.columns]
                        st.dataframe(bids_for_item_df_display[final_display_cols_bids], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum lance cadastrado para este item.")

                st.markdown("---"); st.subheader("Gráficos do Item")
                graph_cols_display = st.columns(2)
                with graph_cols_display[0]:
                    if not quotes_for_item_df_display.empty and 'price' in quotes_for_item_df_display.columns and 'supplier_name' in quotes_for_item_df_display.columns : st.plotly_chart(create_quotes_figure(quotes_for_item_df_display), use_container_width=True)
                    else: st.caption("Gráfico de orçamentos não disponível.")
                with graph_cols_display[1]:
                    if not bids_for_item_df_display.empty and 'price' in bids_for_item_df_display.columns and 'competitor_name' in bids_for_item_df_display.columns:
                        min_quote_price_val = quotes_for_item_df_display['price'].min() if not quotes_for_item_df_display.empty and 'price' in quotes_for_item_df_display.columns else None
                        st.plotly_chart(create_bids_figure(bids_for_item_df_display, min_quote_price_val), use_container_width=True)
                    else: st.caption("Gráfico de lances não disponível.")
            else:
                if st.session_state.selected_item_id is not None:
                    st.warning("Item selecionado não é válido para a licitação atual ou foi removido.")
                    # Não reseta aqui para permitir que o selectbox tente se corrigir no próximo rerun
    except IndexError:
        st.warning("Ocorreu um erro ao tentar exibir os detalhes do item.")
        if st.session_state.selected_item_id is not None:
            st.session_state.selected_item_id = None; st.session_state.selected_item_name_for_display = None

# Abrir diálogos de gerenciamento de Fornecedores/Concorrentes se flags estiverem ativas
if st.session_state.get('show_manage_supplier_dialog', False): manage_supplier_dialog_wrapper()
if st.session_state.get('show_manage_competitor_dialog', False): manage_competitor_dialog_wrapper()
