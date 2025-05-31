import streamlit as st
import pandas as pd
from decimal import Decimal
from typing import Any, cast

from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid
from repository import SQLModelRepository
from state import initialize_session_state
from ui.plotting import create_quotes_figure, create_bids_figure
from ui.utils import get_options_map
from ui.dialogs import (
    manage_bidding_dialog_wrapper,
    manage_item_dialog_wrapper,
    manage_supplier_dialog_wrapper,
    manage_competitor_dialog_wrapper,
    set_dialog_repositories
)

# --- Database Repository Instances ---
db_url = "sqlite:///data/bidtrack.db"

bidding_repo: SQLModelRepository[Bidding] = SQLModelRepository(Bidding, db_url)
item_repo: SQLModelRepository[Item] = SQLModelRepository(Item, db_url)
supplier_repo: SQLModelRepository[Supplier] = SQLModelRepository(Supplier, db_url)
competitor_repo: SQLModelRepository[Competitor] = SQLModelRepository(Competitor, db_url)
quote_repo: SQLModelRepository[Quote] = SQLModelRepository(Quote, db_url)
bid_repo: SQLModelRepository[Bid] = SQLModelRepository(Bid, db_url)

# --- Constants ---
DEFAULT_BIDDING_SELECT_MESSAGE = "Selecione ou Cadastre uma Licitação..."
DEFAULT_ITEM_SELECT_MESSAGE = "Selecione ou Cadastre um Item..."
DEFAULT_SUPPLIER_SELECT_MESSAGE = "Selecione ou Cadastre um Fornecedor..."
DEFAULT_COMPETITOR_SELECT_MESSAGE = "Selecione ou Cadastre um Concorrente..."
APP_TITLE = "📊 Sistema Integrado de Licitações"

# --- Initialize Session State ---
initialize_session_state()

# Initialize dialog repositories
set_dialog_repositories(
    b_repo=bidding_repo, i_repo=item_repo,
    s_repo=supplier_repo, c_repo=competitor_repo,
    q_repo=quote_repo, bi_repo=bid_repo
)

# --- Página Principal da Aplicação ---
_ = st.set_page_config(layout="wide", page_title=APP_TITLE)
_ = st.title(APP_TITLE)

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
all_biddings_list = bidding_repo.get_all()
if all_biddings_list is None:
    all_biddings_list = []

bidding_options_map: dict[int | str | None, str]
bidding_option_ids: list[int | str | None]
bidding_options_map, bidding_option_ids = get_options_map(
    data_list=all_biddings_list,
    extra_cols=['process_number', 'city', 'mode'],
    default_message=DEFAULT_BIDDING_SELECT_MESSAGE
)

with col_bid_select:
    # Assuming session_state.selected_bidding_id is also int | str | None
    current_bidding_id = cast(int | str | None, st.session_state.selected_bidding_id)
    selected_bidding_id_from_sb: int | str | None = st.selectbox(
        "Escolha uma Licitação:",
        options=bidding_option_ids,
        format_func=lambda x: str(bidding_options_map.get(x, DEFAULT_BIDDING_SELECT_MESSAGE)),
        index=bidding_option_ids.index(current_bidding_id) if current_bidding_id in bidding_option_ids else 0,
        key="sb_bidding_main"
    )
with col_bid_manage_btn:
    if st.button("➕ Gerenciar Licitações", key="btn_manage_bids_main", use_container_width=True):
        st.session_state.editing_bidding_id = selected_bidding_id_from_sb 
        st.session_state.show_manage_bidding_dialog = True

if selected_bidding_id_from_sb != st.session_state.selected_bidding_id:
    st.session_state.selected_bidding_id = selected_bidding_id_from_sb
    st.session_state.selected_bidding_name_for_display = bidding_options_map.get(selected_bidding_id_from_sb) if selected_bidding_id_from_sb is not None else None
    st.session_state.selected_item_id = None 
    st.session_state.selected_item_name_for_display = None

if st.session_state.show_manage_bidding_dialog:
    manage_bidding_dialog_wrapper()

# --- Seleção de Item e Botão de Gerenciamento ---
items_for_select: list[Item] = []
if st.session_state.selected_bidding_id is not None:
    col_item_select, col_item_manage_btn = st.columns([5, 2], vertical_alignment="bottom")

    all_items_list = item_repo.get_all()
    if all_items_list is None:
        all_items_list = []
    # Assuming st.session_state.selected_bidding_id is int | str | None after selection
    items_for_select = [item for item in all_items_list if item.bidding_id == st.session_state.selected_bidding_id]

    item_options_map: dict[int | str | None, str]
    item_option_ids: list[int | str | None]
    item_options_map, item_option_ids = get_options_map(
        data_list=items_for_select,
        name_col='name',
        default_message=DEFAULT_ITEM_SELECT_MESSAGE
    )

    with col_item_select:
        bidding_display_label = st.session_state.selected_bidding_name_for_display if st.session_state.selected_bidding_name_for_display else "Licitação Selecionada"
        # Assuming session_state.selected_item_id is also int | str | None
        current_item_id = cast(int | str | None, st.session_state.selected_item_id)
        selected_item_id_from_sb: int | str | None = st.selectbox(
            f"Escolha um Item da Licitação '{bidding_display_label}':",
            options=item_option_ids,
            format_func=lambda x: str(item_options_map.get(x, DEFAULT_ITEM_SELECT_MESSAGE)),
            index=item_option_ids.index(current_item_id) if current_item_id in item_option_ids else 0,
            key="sb_item_main"
        )
    with col_item_manage_btn:
        if st.button("➕ Gerenciar Itens", key="btn_manage_items_main", use_container_width=True):
            st.session_state.parent_bidding_id_for_item_dialog = st.session_state.selected_bidding_id
            st.session_state.editing_item_id = selected_item_id_from_sb 
            st.session_state.show_manage_item_dialog = True

    if selected_item_id_from_sb != st.session_state.selected_item_id:
        st.session_state.selected_item_id = selected_item_id_from_sb
        st.session_state.selected_item_name_for_display = item_options_map.get(selected_item_id_from_sb) if selected_item_id_from_sb is not None else None

if st.session_state.show_manage_item_dialog:
    if st.session_state.parent_bidding_id_for_item_dialog is not None:
        manage_item_dialog_wrapper()
    else:
        st.session_state.show_manage_item_dialog = False

if st.session_state.selected_item_id is not None:
    try:
        if items_for_select:
            current_item_details_list = [item for item in items_for_select if item.id == st.session_state.selected_item_id]
            if current_item_details_list:
                current_item_details: Item = current_item_details_list[0]
                _ = st.markdown(f"**Item Selecionado:** {current_item_details.name} (ID: {st.session_state.selected_item_id})")
                _ = st.markdown(f"**Descrição:** {current_item_details.desc}")
                _ = st.markdown(f"**Quantidade:** {current_item_details.quantity} {current_item_details.unit}")
                _ = st.markdown("---")

                expander_cols = st.columns(2)
                with expander_cols[0]:
                    with st.expander(f"➕ Adicionar Novo Orçamento para {current_item_details.name}", expanded=False):
                        col_supp_select, col_supp_manage = st.columns([3,2], vertical_alignment="bottom")
                        all_suppliers_list = supplier_repo.get_all()
                        if all_suppliers_list is None:
                            all_suppliers_list = []

                        supplier_options_map: dict[int | str | None, str]
                        supplier_option_ids: list[int | str | None]
                        supplier_options_map, supplier_option_ids = get_options_map(
                            data_list=all_suppliers_list,
                            default_message=DEFAULT_SUPPLIER_SELECT_MESSAGE
                        )
                        with col_supp_select:
                            selected_supplier_id_quote_raw: int | str | None = st.selectbox(
                                "Fornecedor*:",
                                options=supplier_option_ids,
                                format_func=lambda x: str(supplier_options_map.get(x, DEFAULT_SUPPLIER_SELECT_MESSAGE)),
                                key="sb_supplier_quote_exp"
                            )
                        with col_supp_manage:
                            if st.button("👤 Ger. Fornecedores", key="btn_manage_suppliers_quote_exp", use_container_width=True):
                                st.session_state.editing_supplier_id = selected_supplier_id_quote_raw
                                st.session_state.show_manage_supplier_dialog = True
                        with st.form(key="new_quote_form"):
                            quote_price = st.number_input("Preço do Orçamento*", min_value=0.01, format="%.2f", key="quote_price_input_exp")
                            quote_margin = st.number_input("Margem*", min_value=0.0, format="%.2f", key="quote_margin_input_exp", help="Valor da margem em decimal. Ex: 0.2 para 20%")
                            quote_notes = st.text_area("Notas do Orçamento", key="quote_notes_input_exp")
                            if st.form_submit_button("💾 Salvar Orçamento"):
                                form_valid = True
                                item_id_to_save: int | None = None
                                supplier_id_to_save: int | None = None
                                current_item_id_for_quote_raw = st.session_state.selected_item_id

                                if current_item_id_for_quote_raw is None:
                                    _ = st.error("Item não selecionado. Não é possível adicionar orçamento.")
                                    form_valid = False
                                else:
                                    try:
                                        item_id_to_save = int(current_item_id_for_quote_raw)
                                    except ValueError:
                                        _ = st.error(f"ID do item inválido: '{current_item_id_for_quote_raw}'.")
                                        form_valid = False

                                if selected_supplier_id_quote_raw is None:
                                    _ = st.error("Fornecedor não selecionado. Não é possível adicionar orçamento.")
                                    form_valid = False
                                else:
                                    try:
                                        supplier_id_to_save = int(selected_supplier_id_quote_raw)
                                    except ValueError:
                                        _ = st.error(f"ID do fornecedor inválido: '{selected_supplier_id_quote_raw}'.")
                                        form_valid = False

                                if not quote_price or quote_price <= 0: # type: ignore
                                    _ = st.error("Preço do orçamento deve ser maior que zero.")
                                    form_valid = False

                                if form_valid and item_id_to_save is not None and supplier_id_to_save is not None:
                                    try:
                                        new_quote = Quote(
                                            item_id=item_id_to_save,
                                            supplier_id=supplier_id_to_save,
                                            price=Decimal(str(quote_price)),
                                            margin=quote_margin,
                                            notes=quote_notes
                                        )
                                        _ = quote_repo.add(new_quote)
                                        _ = st.success(f"Orçamento de {supplier_options_map.get(selected_supplier_id_quote_raw, 'Fornecedor')} adicionado!")
                                        st.rerun()
                                    except Exception as e:
                                        _ = st.error(f"Erro ao salvar orçamento: {e}")
                with expander_cols[1]:
                    with st.expander(f"➕ Adicionar Novo Lance para {current_item_details.name}", expanded=False):
                        col_comp_select, col_comp_manage = st.columns([3,2], vertical_alignment="bottom")
                        all_competitors_list = competitor_repo.get_all()
                        if all_competitors_list is None:
                            all_competitors_list = []

                        competitor_options_map: dict[int | str | None, str]
                        competitor_option_ids: list[int | str | None]
                        competitor_options_map, competitor_option_ids = get_options_map(
                            data_list=all_competitors_list,
                            default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE
                        )
                        with col_comp_select:
                            selected_competitor_id_bid_raw: int | str | None = st.selectbox(
                                "Concorrente*:",
                                options=competitor_option_ids,
                                format_func=lambda x: str(competitor_options_map.get(x, DEFAULT_COMPETITOR_SELECT_MESSAGE)),
                                key="sb_competitor_bid_exp"
                            )
                        with col_comp_manage:
                            if st.button("👤 Ger. Concorrentes", key="btn_manage_competitors_bid_exp", use_container_width=True):
                                st.session_state.editing_competitor_id = selected_competitor_id_bid_raw
                                st.session_state.show_manage_competitor_dialog = True
                        with st.form(key="new_bid_form"):
                            bid_price = st.number_input("Preço do Lance*", min_value=0.01, format="%.2f", key="bid_price_input_exp")
                            bid_notes = st.text_area("Notas do Lance", key="bid_notes_input_exp")
                            if st.form_submit_button("💾 Salvar Lance"):
                                form_valid_bid = True
                                item_id_to_save_bid: int | None = None
                                competitor_id_to_save_bid: int | None = None
                                bidding_id_to_save_bid: int | None = None
                                current_item_id_for_bid_raw = st.session_state.selected_item_id

                                if current_item_id_for_bid_raw is None:
                                    _ = st.error("Item não selecionado. Não é possível adicionar lance.")
                                    form_valid_bid = False
                                else:
                                    try:
                                        item_id_to_save_bid = int(current_item_id_for_bid_raw)
                                    except ValueError:
                                        _ = st.error(f"ID do item inválido: '{current_item_id_for_bid_raw}'.")
                                        form_valid_bid = False

                                if hasattr(current_item_details, 'bidding_id') and current_item_details.bidding_id is not None:
                                    try:
                                        bidding_id_to_save_bid = int(current_item_details.bidding_id)
                                    except (ValueError, TypeError):
                                        _ = st.error(f"Bidding ID ('{current_item_details.bidding_id}') do item é inválido.")
                                        form_valid_bid = False
                                else:
                                    _ = st.error("Bidding ID do item não encontrado ou item não carregado.")
                                    form_valid_bid = False

                                if selected_competitor_id_bid_raw is None:
                                    _ = st.error("Concorrente não selecionado. Não é possível adicionar lance.")
                                    form_valid_bid = False
                                else:
                                    try:
                                        competitor_id_to_save_bid = int(selected_competitor_id_bid_raw)
                                    except ValueError:
                                        _ = st.error(f"ID do concorrente inválido: '{selected_competitor_id_bid_raw}'.")
                                        form_valid_bid = False

                                if not bid_price or bid_price <= 0: # type: ignore
                                    _ = st.error("Preço do lance deve ser maior que zero.")
                                    form_valid_bid = False

                                if form_valid_bid and item_id_to_save_bid is not None and bidding_id_to_save_bid is not None and competitor_id_to_save_bid is not None:
                                    try:
                                        new_bid = Bid(
                                            item_id=item_id_to_save_bid,
                                            bidding_id=bidding_id_to_save_bid,
                                            competitor_id=competitor_id_to_save_bid,
                                            price=Decimal(str(bid_price)),
                                            notes=bid_notes
                                        )
                                        _ = bid_repo.add(new_bid)
                                        _ = st.success(f"Lance de {competitor_options_map.get(selected_competitor_id_bid_raw, 'Concorrente')} adicionado!")
                                        st.rerun()
                                    except Exception as e:
                                        _ = st.error(f"Erro ao salvar lance: {e}")

                all_quotes_list_df = quote_repo.get_all()
                if all_quotes_list_df is None: all_quotes_list_df = []
                quotes_for_item_list = [q for q in all_quotes_list_df if q.item_id == st.session_state.selected_item_id]

                all_bids_list_df = bid_repo.get_all()
                if all_bids_list_df is None: all_bids_list_df = []
                bids_for_item_list = [b for b in all_bids_list_df if b.item_id == st.session_state.selected_item_id]

                quotes_for_item_df_display = pd.DataFrame([q.model_dump() for q in quotes_for_item_list])
                bids_for_item_df_display = pd.DataFrame([b.model_dump() for b in bids_for_item_list])

                if not quotes_for_item_df_display.empty and all_suppliers_list:
                    supplier_map = {s.id: s.name for s in all_suppliers_list}
                    quotes_for_item_df_display['supplier_name'] = quotes_for_item_df_display['supplier_id'].map(supplier_map)

                if not bids_for_item_df_display.empty and all_competitors_list:
                    competitor_map = {c.id: c.name for c in all_competitors_list}
                    bids_for_item_df_display['competitor_name'] = bids_for_item_df_display['competitor_id'].map(competitor_map)

                table_cols_display = st.columns(2) 
                with table_cols_display[0]:
                    _ = st.markdown("##### Orçamentos Recebidos")
                    if not quotes_for_item_df_display.empty:
                        if 'created_at' in quotes_for_item_df_display.columns:
                            quotes_for_item_df_display['created_at'] = pd.to_datetime(quotes_for_item_df_display['created_at'].astype(str), errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                        if 'update_at' in quotes_for_item_df_display.columns and pd.notnull(quotes_for_item_df_display['update_at']).all():
                            quotes_for_item_df_display['update_at'] = pd.to_datetime(quotes_for_item_df_display['update_at'].astype(str), errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                    if not quotes_for_item_df_display.empty:
                        _ = st.dataframe(quotes_for_item_df_display[['supplier_name', 'price', 'created_at', 'update_at', 'notes']], hide_index=True, use_container_width=True)
                    else:
                        _ = st.info("Nenhum orçamento cadastrado para este item.")
                with table_cols_display[1]:
                    _ = st.markdown("##### Lances Recebidos")
                    if not bids_for_item_df_display.empty:
                        bids_to_show = bids_for_item_df_display.copy() 
                        if 'created_at' in bids_to_show.columns:
                            bids_to_show['created_at'] = pd.to_datetime(bids_to_show['created_at'].astype(str), errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                        if 'update_at' in bids_to_show.columns and pd.notnull(bids_to_show['update_at']).all():
                            bids_to_show['update_at'] = pd.to_datetime(bids_to_show['update_at'].astype(str), errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                        _ = st.dataframe(bids_to_show[['competitor_name', 'price', 'created_at', 'notes', 'update_at']], hide_index=True, use_container_width=True)
                    else:
                        _ = st.info("Nenhum lance cadastrado para este item.")

                _ = st.markdown("---")
                _ = st.subheader("Gráficos do Item")
                graph_cols_display = st.columns(2)
                with graph_cols_display[0]:
                    if not quotes_for_item_df_display.empty:
                        _ = st.plotly_chart(create_quotes_figure(quotes_for_item_df_display), use_container_width=True)
                    else:
                        _ = st.caption("Gráfico de orçamentos não disponível.")
                with graph_cols_display[1]:
                    if not bids_for_item_df_display.empty and 'price' in bids_for_item_df_display.columns:
                        min_quote_price_val = quotes_for_item_df_display['price'].min() if not quotes_for_item_df_display.empty and 'price' in quotes_for_item_df_display.columns else None
                        _ = st.plotly_chart(create_bids_figure(bids_for_item_df_display, min_quote_price_val), use_container_width=True)
                    else:
                        _ = st.caption("Gráfico de lances não disponível.")
            else:
                if st.session_state.selected_item_id is not None:
                    _ = st.warning("Item selecionado não é válido para a licitação atual ou foi removido.")
    except IndexError:
        _ = st.warning("Ocorreu um erro ao tentar exibir os detalhes do item.")
        if st.session_state.selected_item_id is not None:
            st.session_state.selected_item_id = None
            st.session_state.selected_item_name_for_display = None

if st.session_state.get('show_manage_supplier_dialog', False):
    manage_supplier_dialog_wrapper()
if st.session_state.get('show_manage_competitor_dialog', False):
    manage_competitor_dialog_wrapper()
