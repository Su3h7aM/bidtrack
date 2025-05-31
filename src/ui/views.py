import streamlit as st
import pandas as pd
from repository import SQLModelRepository
from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid, BiddingMode
from typing import List

# [render_licitacoes_tab function code - assumed to be here and correct]

def render_licitacoes_tab(bidding_repo: SQLModelRepository[Bidding]):
    st.subheader("Consultar Licitações")

    all_biddings_models: List[Bidding] = bidding_repo.get_all()

    if not all_biddings_models:
        st.info("Nenhuma licitação cadastrada.")
        return

    biddings_data = [b.model_dump() for b in all_biddings_models]
    df_biddings = pd.DataFrame(biddings_data)

    for col_date in ['date', 'created_at', 'updated_at']:
        if col_date in df_biddings.columns:
            df_biddings[col_date] = pd.to_datetime(df_biddings[col_date], errors='coerce')

    st.sidebar.header("Filtros para Licitações")

    unique_cities_list = ["Todas"] + sorted(df_biddings['city'].astype(str).unique())
    selected_city = st.sidebar.selectbox(
        "Cidade",
        options=unique_cities_list,
        index=0,
        key="licitacoes_city_filter"
    )

    min_date_val, max_date_val = None, None
    if 'date' in df_biddings.columns and not df_biddings['date'].isnull().all():
        min_date_val = df_biddings['date'].min().date()
        max_date_val = df_biddings['date'].max().date()

    col_date_start, col_date_end = st.sidebar.columns(2)
    selected_start_date = col_date_start.date_input(
        "Data Início",
        value=min_date_val,
        min_value=min_date_val,
        max_value=max_date_val,
        key="licitacoes_start_date_filter"
    )
    selected_end_date = col_date_end.date_input(
        "Data Fim",
        value=max_date_val,
        min_value=min_date_val,
        max_value=max_date_val,
        key="licitacoes_end_date_filter"
    )

    search_term = st.sidebar.text_input(
        "Buscar (Nº Processo, Cidade)",
        key="licitacoes_search_filter"
    ).lower()

    filtered_df = df_biddings.copy()

    if selected_city != "Todas":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]

    if 'date' in filtered_df.columns and not filtered_df['date'].isnull().all():
        filtered_df['date'] = pd.to_datetime(filtered_df['date'], errors='coerce')
        if selected_start_date:
            valid_dates_mask = filtered_df['date'].notna()
            if valid_dates_mask.any():
                 filtered_df = filtered_df[valid_dates_mask & (filtered_df.loc[valid_dates_mask, 'date'].dt.date >= selected_start_date)]
        if selected_end_date:
            valid_dates_mask = filtered_df['date'].notna()
            if valid_dates_mask.any():
                filtered_df = filtered_df[valid_dates_mask & (filtered_df.loc[valid_dates_mask, 'date'].dt.date <= selected_end_date)]

    if search_term:
        search_condition = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        if 'process_number' in filtered_df.columns:
            search_condition |= filtered_df['process_number'].astype(str).str.lower().str.contains(search_term)
        if 'city' in filtered_df.columns:
            search_condition |= filtered_df['city'].astype(str).str.lower().str.contains(search_term)
        if search_condition.any():
            filtered_df = filtered_df[search_condition]
        elif not search_condition.all() and search_term:
             filtered_df = filtered_df.iloc[0:0]


    if filtered_df.empty:
        st.warning("Nenhuma licitação encontrada com os filtros aplicados.")
    else:
        display_df = filtered_df.copy()

        if 'mode' in display_df.columns:
            display_df['mode'] = display_df['mode'].apply(lambda m: m.value if isinstance(m, BiddingMode) else m)

        date_columns_to_format_map = {
            'date': 'Data da Sessão',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em'
        }
        for original_col_name, display_col_name in date_columns_to_format_map.items():
            if original_col_name in display_df.columns:
                display_df[original_col_name] = pd.to_datetime(display_df[original_col_name], errors='coerce')
                display_df[display_col_name] = display_df[original_col_name].dt.strftime('%d/%m/%Y %H:%M:%S')
                display_df[display_col_name] = display_df[display_col_name].fillna('N/A')
                display_df[display_col_name] = display_df[display_col_name].astype(str).replace({'NaT': 'N/A'})

        final_columns_to_display_map = {
            'process_number': 'Nº Processo',
            'city': 'Cidade',
            'mode': 'Modalidade',
            'Data da Sessão': 'Data da Sessão',
            'Criado em': 'Criado em',
            'Atualizado em': 'Atualizado em'
        }

        columns_for_st_dataframe = [col for col in final_columns_to_display_map.keys() if col in display_df.columns]
        renamed_df_for_display = display_df[columns_for_st_dataframe].rename(columns=final_columns_to_display_map)

        st.dataframe(
            renamed_df_for_display,
            hide_index=True,
            use_container_width=True
        )


# [render_itens_tab function code - assumed to be here and correct]

def render_itens_tab(item_repo: SQLModelRepository[Item], bidding_repo: SQLModelRepository[Bidding]):
    st.subheader("Consultar Itens de Licitação")

    all_items_models: List[Item] = item_repo.get_all()
    all_biddings_models: List[Bidding] = bidding_repo.get_all()

    if not all_items_models:
        st.info("Nenhum item de licitação cadastrado.")
        return

    items_data = [item.model_dump() for item in all_items_models]
    df_items = pd.DataFrame(items_data)

    if not all_biddings_models:
        st.warning("Dados das licitações não encontrados. Informações da licitação nos itens podem estar ausentes.")
        df_biddings_processed = pd.DataFrame(columns=['bidding_id_ref', 'bidding_process_number', 'bidding_city', 'bidding_session_date'])
    else:
        biddings_data = [bidding.model_dump() for bidding in all_biddings_models]
        df_biddings_processed = pd.DataFrame(biddings_data)
        if 'id' not in df_biddings_processed.columns:
             df_biddings_processed['id'] = None

        df_biddings_processed = df_biddings_processed.rename(columns={
            'id': 'bidding_id_ref',
            'process_number': 'bidding_process_number',
            'city': 'bidding_city',
            'date': 'bidding_session_date'
        })
        cols_to_keep_bidding = ['bidding_id_ref', 'bidding_process_number', 'bidding_city', 'bidding_session_date']
        df_biddings_processed = df_biddings_processed[[col for col in cols_to_keep_bidding if col in df_biddings_processed.columns]]

    if 'bidding_id' in df_items.columns and 'bidding_id_ref' in df_biddings_processed.columns and not df_biddings_processed.empty:
        df_items['bidding_id'] = df_items['bidding_id'].astype(str)
        df_biddings_processed['bidding_id_ref'] = df_biddings_processed['bidding_id_ref'].astype(str)
        df_merged = pd.merge(df_items, df_biddings_processed, left_on='bidding_id', right_on='bidding_id_ref', how='left')
    else:
        df_merged = df_items.copy()
        if 'bidding_process_number' not in df_merged.columns: df_merged['bidding_process_number'] = "N/A"
        if 'bidding_city' not in df_merged.columns: df_merged['bidding_city'] = "N/A"
        if 'bidding_session_date' not in df_merged.columns: df_merged['bidding_session_date'] = pd.NaT

    if 'created_at' in df_merged.columns:
        df_merged.rename(columns={'created_at': 'created_at_item'}, inplace=True)
    if 'updated_at' in df_merged.columns:
        df_merged.rename(columns={'updated_at': 'updated_at_item'}, inplace=True)

    date_cols_in_merged = ['created_at_item', 'updated_at_item', 'bidding_session_date']
    for col_date_item in date_cols_in_merged:
        if col_date_item in df_merged.columns:
            df_merged[col_date_item] = pd.to_datetime(df_merged[col_date_item], errors='coerce')

    st.sidebar.header("Filtros para Itens")

    bidding_options_display_map = {}
    if 'bidding_id' in df_merged.columns and 'bidding_process_number' in df_merged.columns:
        unique_biddings_info = df_merged[['bidding_id', 'bidding_process_number', 'bidding_city']].copy()
        unique_biddings_info.dropna(subset=['bidding_id', 'bidding_process_number'], inplace=True)
        unique_biddings_info.drop_duplicates(subset=['bidding_id'], inplace=True)

        bidding_options_display_map = {
            str(row['bidding_id']): f"{row['bidding_process_number']} - {row['bidding_city'] if pd.notna(row['bidding_city']) else 'N/A'}"
            for _, row in unique_biddings_info.iterrows()
        }

    selected_bidding_ids_for_item_filter = []
    if bidding_options_display_map:
        selected_bidding_ids_for_item_filter = st.sidebar.multiselect(
            "Licitação (Nº Processo - Cidade)",
            options=list(bidding_options_display_map.keys()),
            format_func=lambda x: bidding_options_display_map[x],
            key="itens_bidding_filter"
        )

    search_term_item_filter = st.sidebar.text_input(
        "Buscar (Nome, Descrição do Item)",
        key="itens_search_filter"
    ).lower()

    filtered_df_items_view = df_merged.copy()

    if selected_bidding_ids_for_item_filter:
        filtered_df_items_view['bidding_id'] = filtered_df_items_view['bidding_id'].astype(str)
        filtered_df_items_view = filtered_df_items_view[filtered_df_items_view['bidding_id'].isin(selected_bidding_ids_for_item_filter)]

    if search_term_item_filter:
        item_search_cond = pd.Series([False] * len(filtered_df_items_view), index=filtered_df_items_view.index)
        if 'name' in filtered_df_items_view.columns:
             item_search_cond |= filtered_df_items_view['name'].astype(str).str.lower().str.contains(search_term_item_filter)
        if 'desc' in filtered_df_items_view.columns:
             item_search_cond |= filtered_df_items_view['desc'].astype(str).str.lower().str.contains(search_term_item_filter)
        if item_search_cond.any():
            filtered_df_items_view = filtered_df_items_view[item_search_cond]
        elif not item_search_cond.all() and search_term_item_filter:
            filtered_df_items_view = filtered_df_items_view.iloc[0:0]

    if filtered_df_items_view.empty:
        st.warning("Nenhum item encontrado com os filtros aplicados.")
    else:
        display_ready_df_items = filtered_df_items_view.copy()

        date_cols_to_format_for_items = {
            'bidding_session_date': 'Data Licitação',
            'created_at_item': 'Item Criado em',
            'updated_at_item': 'Item Atualizado em'
        }
        for col_orig, col_display_name in date_cols_to_format_for_items.items():
            if col_orig in display_ready_df_items.columns:
                display_ready_df_items[col_orig] = pd.to_datetime(display_ready_df_items[col_orig], errors='coerce')
                display_ready_df_items[col_display_name] = display_ready_df_items[col_orig].dt.strftime('%d/%m/%Y %H:%M:%S')
                display_ready_df_items[col_display_name] = display_ready_df_items[col_display_name].fillna('N/A')
                display_ready_df_items[col_display_name] = display_ready_df_items[col_display_name].astype(str).replace({'NaT': 'N/A'})

        final_item_display_columns_map = {
            'bidding_process_number': 'Nº Processo Licitação',
            'bidding_city': 'Cidade Licitação',
            'Data Licitação': 'Data Licitação',
            'name': 'Nome do Item',
            'desc': 'Descrição do Item',
            'quantity': 'Quantidade',
            'unit': 'Unidade',
            'Item Criado em': 'Item Criado em',
            'Item Atualizado em': 'Item Atualizado em'
        }

        cols_for_final_item_df = [col_name for col_name in final_item_display_columns_map.keys() if col_name in display_ready_df_items.columns]
        final_renamed_item_df = display_ready_df_items[cols_for_final_item_df].rename(columns=final_item_display_columns_map)

        st.dataframe(
            final_renamed_item_df,
            hide_index=True,
            use_container_width=True
        )

# [render_orcamentos_tab function code - assumed to be here and correct]

def render_orcamentos_tab(quote_repo: SQLModelRepository[Quote], item_repo: SQLModelRepository[Item], supplier_repo: SQLModelRepository[Supplier]):
    st.subheader("Consultar Orçamentos")

    all_quotes_models: List[Quote] = quote_repo.get_all()
    all_items_models: List[Item] = item_repo.get_all()
    all_suppliers_models: List[Supplier] = supplier_repo.get_all()

    if not all_quotes_models:
        st.info("Nenhum orçamento cadastrado.")
        return

    quotes_data = [quote.model_dump() for quote in all_quotes_models]
    df_quotes = pd.DataFrame(quotes_data)

    if not all_items_models:
        st.warning("Dados dos itens não encontrados. Informações do item nos orçamentos podem estar ausentes.")
        df_items_processed = pd.DataFrame(columns=['item_id_ref', 'item_name', 'item_desc'])
    else:
        items_data_proc = [item.model_dump() for item in all_items_models]
        df_items_processed = pd.DataFrame(items_data_proc)
        df_items_processed = df_items_processed.rename(columns={'id': 'item_id_ref', 'name': 'item_name', 'desc': 'item_desc'})
        # Ensure only specified columns are kept to avoid clashes
        df_items_processed = df_items_processed[['item_id_ref', 'item_name', 'item_desc']]

    if not all_suppliers_models:
        st.warning("Dados dos fornecedores não encontrados. Informações do fornecedor nos orçamentos podem estar ausentes.")
        df_suppliers_processed = pd.DataFrame(columns=['supplier_id_ref', 'supplier_name'])
    else:
        suppliers_data_proc = [supplier.model_dump() for supplier in all_suppliers_models]
        df_suppliers_processed = pd.DataFrame(suppliers_data_proc)
        df_suppliers_processed = df_suppliers_processed.rename(columns={'id': 'supplier_id_ref', 'name': 'supplier_name'})
        df_suppliers_processed = df_suppliers_processed[['supplier_id_ref', 'supplier_name']]

    df_merged_quotes = df_quotes
    if 'item_id' in df_merged_quotes.columns and 'item_id_ref' in df_items_processed.columns and not df_items_processed.empty:
        df_merged_quotes['item_id'] = df_merged_quotes['item_id'].astype(str)
        df_items_processed['item_id_ref'] = df_items_processed['item_id_ref'].astype(str)
        df_merged_quotes = pd.merge(df_merged_quotes, df_items_processed, left_on='item_id', right_on='item_id_ref', how='left')

    if 'supplier_id' in df_merged_quotes.columns and 'supplier_id_ref' in df_suppliers_processed.columns and not df_suppliers_processed.empty:
        df_merged_quotes['supplier_id'] = df_merged_quotes['supplier_id'].astype(str)
        df_suppliers_processed['supplier_id_ref'] = df_suppliers_processed['supplier_id_ref'].astype(str)
        df_merged_quotes = pd.merge(df_merged_quotes, df_suppliers_processed, left_on='supplier_id', right_on='supplier_id_ref', how='left')

    for col in ['item_name', 'item_desc', 'supplier_name']:
        if col not in df_merged_quotes.columns:
            df_merged_quotes[col] = 'N/A'

    if 'created_at' in df_merged_quotes.columns:
        df_merged_quotes.rename(columns={'created_at': 'created_at_quote'}, inplace=True)
    if 'updated_at' in df_merged_quotes.columns:
        df_merged_quotes.rename(columns={'updated_at': 'updated_at_quote'}, inplace=True)

    for col_date_quote in ['created_at_quote', 'updated_at_quote']:
        if col_date_quote in df_merged_quotes.columns:
            df_merged_quotes[col_date_quote] = pd.to_datetime(df_merged_quotes[col_date_quote], errors='coerce')

    st.sidebar.header("Filtros para Orçamentos")

    item_options_map = {}
    if 'item_id' in df_merged_quotes.columns and 'item_name' in df_merged_quotes.columns:
        unique_items = df_merged_quotes[['item_id', 'item_name']].copy()
        unique_items.dropna(subset=['item_id','item_name'], inplace=True) # Ensure both id and name are present for map
        unique_items.drop_duplicates(subset=['item_id'], inplace=True)
        item_options_map = {str(row['item_id']): row['item_name'] for _, row in unique_items.iterrows()}

    selected_item_ids_for_quote_filter = []
    if item_options_map:
        selected_item_ids_for_quote_filter = st.sidebar.multiselect(
            "Item (Orçamento)", # Clarified filter title
            options=list(item_options_map.keys()),
            format_func=lambda x: item_options_map[x],
            key="quotes_item_filter"
        )

    supplier_options_map = {}
    if 'supplier_id' in df_merged_quotes.columns and 'supplier_name' in df_merged_quotes.columns:
        unique_suppliers = df_merged_quotes[['supplier_id', 'supplier_name']].copy()
        unique_suppliers.dropna(subset=['supplier_id','supplier_name'], inplace=True)
        unique_suppliers.drop_duplicates(subset=['supplier_id'], inplace=True)
        supplier_options_map = {str(row['supplier_id']): row['supplier_name'] for _, row in unique_suppliers.iterrows()}

    selected_supplier_ids_for_quote_filter = []
    if supplier_options_map:
        selected_supplier_ids_for_quote_filter = st.sidebar.multiselect(
            "Fornecedor (Orçamento)", # Clarified filter title
            options=list(supplier_options_map.keys()),
            format_func=lambda x: supplier_options_map[x],
            key="quotes_supplier_filter"
        )

    search_term_quote_notes = st.sidebar.text_input(
        "Buscar nas Notas do Orçamento",
        key="quotes_notes_search"
    ).lower()

    filtered_df_quotes_view = df_merged_quotes.copy()

    if selected_item_ids_for_quote_filter:
        filtered_df_quotes_view['item_id'] = filtered_df_quotes_view['item_id'].astype(str)
        filtered_df_quotes_view = filtered_df_quotes_view[filtered_df_quotes_view['item_id'].isin(selected_item_ids_for_quote_filter)]

    if selected_supplier_ids_for_quote_filter:
        filtered_df_quotes_view['supplier_id'] = filtered_df_quotes_view['supplier_id'].astype(str)
        filtered_df_quotes_view = filtered_df_quotes_view[filtered_df_quotes_view['supplier_id'].isin(selected_supplier_ids_for_quote_filter)]

    if search_term_quote_notes:
        if 'notes' in filtered_df_quotes_view.columns and filtered_df_quotes_view['notes'].notna().any():
            filtered_df_quotes_view = filtered_df_quotes_view[filtered_df_quotes_view['notes'].astype(str).str.lower().str.contains(search_term_quote_notes)]
        elif search_term_quote_notes: # Search term provided but no 'notes' column or all notes are NaN
             filtered_df_quotes_view = filtered_df_quotes_view.iloc[0:0]

    if filtered_df_quotes_view.empty:
        st.warning("Nenhum orçamento encontrado com os filtros aplicados.")
    else:
        display_ready_df_quotes = filtered_df_quotes_view.copy()

        date_cols_to_format_for_quotes = {
            'created_at_quote': 'Orçamento Criado em',
            'updated_at_quote': 'Orçamento Atualizado em'
        }
        for col_orig, col_display_name in date_cols_to_format_for_quotes.items():
            if col_orig in display_ready_df_quotes.columns:
                display_ready_df_quotes[col_orig] = pd.to_datetime(display_ready_df_quotes[col_orig], errors='coerce')
                display_ready_df_quotes[col_display_name] = display_ready_df_quotes[col_orig].dt.strftime('%d/%m/%Y %H:%M:%S')
                display_ready_df_quotes[col_display_name] = display_ready_df_quotes[col_display_name].fillna('N/A')
                display_ready_df_quotes[col_display_name] = display_ready_df_quotes[col_display_name].astype(str).replace({'NaT': 'N/A'})

        # Prepare for formatting price and margin
        final_quote_display_columns_map = {
            'item_name': 'Nome do Item',
            'supplier_name': 'Fornecedor',
            'price': 'Preço Orçado (R$)', # Placeholder, will be replaced by formatted column
            'margin': 'Margem (%)',     # Placeholder, will be replaced by formatted column
            'notes': 'Notas do Orçamento',
            'Orçamento Criado em': 'Orçamento Criado em',
            'Orçamento Atualizado em': 'Orçamento Atualizado em'
        }

        if 'price' in display_ready_df_quotes.columns:
            display_ready_df_quotes['Preço Orçado (R$)_formatted'] = display_ready_df_quotes['price'].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else 'N/A')
            final_quote_display_columns_map['Preço Orçado (R$)_formatted'] = 'Preço Orçado (R$)' # Update map to use new formatted column
            if 'price' in final_quote_display_columns_map: # check before deleting
                del final_quote_display_columns_map['price'] # Remove old key

        if 'margin' in display_ready_df_quotes.columns:
            # Ensure margin is float before attempting multiplication
            def format_margin(x):
                if pd.notna(x):
                    try:
                        return f"{float(x)*100:.2f}%"
                    except ValueError: # Handles cases where x might be a non-convertible string
                        return 'N/A'
                return 'N/A'
            display_ready_df_quotes['Margem (%)_formatted'] = display_ready_df_quotes['margin'].apply(format_margin)
            final_quote_display_columns_map['Margem (%)_formatted'] = 'Margem (%)'
            if 'margin' in final_quote_display_columns_map: # check before deleting
                del final_quote_display_columns_map['margin']

        cols_for_final_quote_df = [col_name for col_name in final_quote_display_columns_map.keys() if col_name in display_ready_df_quotes.columns]
        final_renamed_quote_df = display_ready_df_quotes[cols_for_final_quote_df].rename(columns=final_quote_display_columns_map)

        st.dataframe(
            final_renamed_quote_df,
            hide_index=True,
            use_container_width=True
        )

def render_lances_tab(bid_repo: SQLModelRepository[Bid], item_repo: SQLModelRepository[Item], competitor_repo: SQLModelRepository[Competitor]):
    st.subheader("Consultar Lances")

    all_bids_models: List[Bid] = bid_repo.get_all()
    all_items_models: List[Item] = item_repo.get_all()
    all_competitors_models: List[Competitor] = competitor_repo.get_all()

    if not all_bids_models:
        st.info("Nenhum lance cadastrado.")
        return

    bids_data = [bid.model_dump() for bid in all_bids_models]
    df_bids = pd.DataFrame(bids_data)

    # Prepare items DataFrame for merge
    if not all_items_models:
        st.warning("Dados dos itens não encontrados. Informações do item nos lances podem estar ausentes.")
        df_items_processed = pd.DataFrame(columns=['item_id_ref', 'item_name', 'item_desc'])
    else:
        items_data_proc = [item.model_dump() for item in all_items_models]
        df_items_processed = pd.DataFrame(items_data_proc)
        df_items_processed = df_items_processed.rename(columns={'id': 'item_id_ref', 'name': 'item_name', 'desc': 'item_desc'})
        df_items_processed = df_items_processed[['item_id_ref', 'item_name', 'item_desc']]

    # Prepare competitors DataFrame for merge
    if not all_competitors_models:
        st.warning("Dados dos concorrentes não encontrados. Informações do concorrente nos lances podem estar ausentes.")
        df_competitors_processed = pd.DataFrame(columns=['competitor_id_ref', 'competitor_name'])
    else:
        competitors_data_proc = [competitor.model_dump() for competitor in all_competitors_models]
        df_competitors_processed = pd.DataFrame(competitors_data_proc)
        df_competitors_processed = df_competitors_processed.rename(columns={'id': 'competitor_id_ref', 'name': 'competitor_name'})
        df_competitors_processed = df_competitors_processed[['competitor_id_ref', 'competitor_name']]

    # Merge bids with items and competitors
    df_merged_bids = df_bids
    if 'item_id' in df_merged_bids.columns and 'item_id_ref' in df_items_processed.columns and not df_items_processed.empty:
        df_merged_bids['item_id'] = df_merged_bids['item_id'].astype(str)
        df_items_processed['item_id_ref'] = df_items_processed['item_id_ref'].astype(str)
        df_merged_bids = pd.merge(df_merged_bids, df_items_processed, left_on='item_id', right_on='item_id_ref', how='left')

    if 'competitor_id' in df_merged_bids.columns and 'competitor_id_ref' in df_competitors_processed.columns and not df_competitors_processed.empty:
        df_merged_bids['competitor_id'] = df_merged_bids['competitor_id'].astype(str)
        df_competitors_processed['competitor_id_ref'] = df_competitors_processed['competitor_id_ref'].astype(str)
        df_merged_bids = pd.merge(df_merged_bids, df_competitors_processed, left_on='competitor_id', right_on='competitor_id_ref', how='left')

    for col in ['item_name', 'item_desc', 'competitor_name']: # Ensure these columns exist after merge
        if col not in df_merged_bids.columns:
            df_merged_bids[col] = 'N/A'

    if 'created_at' in df_merged_bids.columns:
        df_merged_bids.rename(columns={'created_at': 'created_at_bid'}, inplace=True)
    if 'updated_at' in df_merged_bids.columns:
        df_merged_bids.rename(columns={'updated_at': 'updated_at_bid'}, inplace=True)

    for col_date_bid in ['created_at_bid', 'updated_at_bid']:
        if col_date_bid in df_merged_bids.columns:
            df_merged_bids[col_date_bid] = pd.to_datetime(df_merged_bids[col_date_bid], errors='coerce')

    st.sidebar.header("Filtros para Lances")

    item_options_map_bids = {}
    if 'item_id' in df_merged_bids.columns and 'item_name' in df_merged_bids.columns:
        unique_items_bids = df_merged_bids[['item_id', 'item_name']].copy()
        unique_items_bids.dropna(subset=['item_id', 'item_name'], inplace=True)
        unique_items_bids.drop_duplicates(subset=['item_id'], inplace=True)
        item_options_map_bids = {str(row['item_id']): row['item_name'] for _, row in unique_items_bids.iterrows()}

    selected_item_ids_for_bid_filter = []
    if item_options_map_bids:
        selected_item_ids_for_bid_filter = st.sidebar.multiselect(
            "Item (Lance)",
            options=list(item_options_map_bids.keys()),
            format_func=lambda x: item_options_map_bids[x],
            key="bids_item_filter"
        )

    competitor_options_map = {}
    if 'competitor_id' in df_merged_bids.columns and 'competitor_name' in df_merged_bids.columns:
        unique_competitors = df_merged_bids[['competitor_id', 'competitor_name']].copy()
        unique_competitors.dropna(subset=['competitor_id', 'competitor_name'], inplace=True)
        unique_competitors.drop_duplicates(subset=['competitor_id'], inplace=True)
        competitor_options_map = {str(row['competitor_id']): row['competitor_name'] for _, row in unique_competitors.iterrows()}

    selected_competitor_ids_for_bid_filter = []
    if competitor_options_map:
        selected_competitor_ids_for_bid_filter = st.sidebar.multiselect(
            "Concorrente (Lance)",
            options=list(competitor_options_map.keys()),
            format_func=lambda x: competitor_options_map[x],
            key="bids_competitor_filter"
        )

    search_term_bid_notes = st.sidebar.text_input(
        "Buscar nas Notas do Lance",
        key="bids_notes_search"
    ).lower()

    filtered_df_bids_view = df_merged_bids.copy()

    if selected_item_ids_for_bid_filter:
        filtered_df_bids_view['item_id'] = filtered_df_bids_view['item_id'].astype(str)
        filtered_df_bids_view = filtered_df_bids_view[filtered_df_bids_view['item_id'].isin(selected_item_ids_for_bid_filter)]

    if selected_competitor_ids_for_bid_filter:
        filtered_df_bids_view['competitor_id'] = filtered_df_bids_view['competitor_id'].astype(str)
        filtered_df_bids_view = filtered_df_bids_view[filtered_df_bids_view['competitor_id'].isin(selected_competitor_ids_for_bid_filter)]

    if search_term_bid_notes:
        if 'notes' in filtered_df_bids_view.columns and filtered_df_bids_view['notes'].notna().any():
            filtered_df_bids_view = filtered_df_bids_view[filtered_df_bids_view['notes'].astype(str).str.lower().str.contains(search_term_bid_notes)]
        elif search_term_bid_notes:
             filtered_df_bids_view = filtered_df_bids_view.iloc[0:0]

    if filtered_df_bids_view.empty:
        st.warning("Nenhum lance encontrado com os filtros aplicados.")
    else:
        display_ready_df_bids = filtered_df_bids_view.copy()

        date_cols_to_format_for_bids = {
            'created_at_bid': 'Lance Criado em',
            'updated_at_bid': 'Lance Atualizado em'
        }
        for col_orig, col_display_name in date_cols_to_format_for_bids.items():
            if col_orig in display_ready_df_bids.columns:
                display_ready_df_bids[col_orig] = pd.to_datetime(display_ready_df_bids[col_orig], errors='coerce')
                display_ready_df_bids[col_display_name] = display_ready_df_bids[col_orig].dt.strftime('%d/%m/%Y %H:%M:%S')
                display_ready_df_bids[col_display_name] = display_ready_df_bids[col_display_name].fillna('N/A')
                display_ready_df_bids[col_display_name] = display_ready_df_bids[col_display_name].astype(str).replace({'NaT': 'N/A'})

        final_bid_display_columns_map = {
            'item_name': 'Nome do Item',
            'competitor_name': 'Concorrente',
            'price': 'Preço do Lance (R$)', # Placeholder, will be formatted
            'notes': 'Notas do Lance',
            'Lance Criado em': 'Lance Criado em',
            'Lance Atualizado em': 'Lance Atualizado em'
        }

        if 'price' in display_ready_df_bids.columns:
            display_ready_df_bids['Preço do Lance (R$)_formatted'] = display_ready_df_bids['price'].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else 'N/A')
            final_bid_display_columns_map['Preço do Lance (R$)_formatted'] = 'Preço do Lance (R$)'
            if 'price' in final_bid_display_columns_map: # check before deleting
                del final_bid_display_columns_map['price']

        cols_for_final_bid_df = [col_name for col_name in final_bid_display_columns_map.keys() if col_name in display_ready_df_bids.columns]
        final_renamed_bid_df = display_ready_df_bids[cols_for_final_bid_df].rename(columns=final_bid_display_columns_map)

        st.dataframe(
            final_renamed_bid_df,
            hide_index=True,
            use_container_width=True
        )

```
