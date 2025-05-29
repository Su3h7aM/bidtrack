import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time

# --- Constantes ---
DEFAULT_BIDDING_SELECT_MESSAGE = "Selecione ou Cadastre uma Licitação..."
DEFAULT_ITEM_SELECT_MESSAGE = "Selecione ou Cadastre um Item..."
DEFAULT_SUPPLIER_SELECT_MESSAGE = "Selecione ou Cadastre um Fornecedor..."
DEFAULT_COMPETITOR_SELECT_MESSAGE = "Selecione ou Cadastre um Concorrente..."
APP_TITLE = "📊 Sistema Integrado de Licitações"

# --- Inicialização do Session State ---
# IDs Selecionados
if 'selected_bidding_id' not in st.session_state: st.session_state.selected_bidding_id = None
if 'selected_item_id' not in st.session_state: st.session_state.selected_item_id = None
# Nomes para exibição (para evitar re-lookup constante se o ID já está no estado)
if 'selected_bidding_name_for_display' not in st.session_state: st.session_state.selected_bidding_name_for_display = None
if 'selected_item_name_for_display' not in st.session_state: st.session_state.selected_item_name_for_display = None


# Bases de Dados em Memória
if 'db_biddings' not in st.session_state:
    mock_initial_biddings = [
        {'id': 1, 'process_number': '18/2025', 'city': 'Rubiataba', 'mode': 'Pregão Eletrônico', 'session_date': pd.to_datetime('2025-06-26').date(), 'session_time': pd.to_datetime('08:00:00', format='%H:%M:%S').time(), 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 2, 'process_number': '23/2025', 'city': 'Ceres', 'mode': 'Tomada de Preços', 'session_date': pd.to_datetime('2025-05-22').date(), 'session_time': pd.to_datetime('09:30:00', format='%H:%M:%S').time(), 'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]
    st.session_state.db_biddings = pd.DataFrame(mock_initial_biddings)
    st.session_state.db_biddings['session_date'] = pd.to_datetime(st.session_state.db_biddings['session_date'], errors='coerce').dt.date
    st.session_state.db_biddings['session_time'] = st.session_state.db_biddings['session_time'].apply(lambda x: pd.to_datetime(x, format='%H:%M:%S').time() if pd.notnull(x) and isinstance(x, str) else (x if isinstance(x, time) else None))

if 'db_items' not in st.session_state:
    mock_initial_items = [
        {'id': 101, 'bidding_id': 1, 'name': 'Drone DJI Mavic Pro', 'description': 'Drone profissional com câmera 4K.', 'quantity': 2, 'unit': 'UN', 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 102, 'bidding_id': 1, 'name': 'Monitor LED 27" Full HD', 'description': 'Monitor para computador.', 'quantity': 5, 'unit': 'UN', 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 201, 'bidding_id': 2, 'name': 'Cadeira de Escritório Ergonômica', 'description': 'Cadeira giratória.', 'quantity': 10, 'unit': 'UN', 'created_at': datetime.now(), 'updated_at': datetime.now()}
    ]
    st.session_state.db_items = pd.DataFrame(mock_initial_items)

if 'db_suppliers' not in st.session_state:
    mock_initial_suppliers = [
        {'id': 1, 'name': 'Fornecedor TechStore', 'website': 'techstore.com', 'email': 'contato@techstore.com', 'phone': '62999990001', 'description': 'Especialista em eletrônicos.', 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 2, 'name': 'Móveis Conforto Total', 'website': 'moveisconforto.com.br', 'email': 'vendas@moveisconforto.com.br', 'phone': '62999990002', 'description': 'Móveis para escritório.', 'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]
    st.session_state.db_suppliers = pd.DataFrame(mock_initial_suppliers)

if 'db_competitors' not in st.session_state:
    mock_initial_competitors = [
        {'id': 1, 'name': 'Concorrente Alfa Drones', 'website': 'alfadrones.com', 'email': 'comercial@alfadrones.com', 'phone': '11988880001', 'description': 'Forte em drones.', 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 2, 'name': 'Concorrente X Displays', 'website': 'xdisplays.com', 'email': 'contato@xdisplays.com', 'phone': '21988880002', 'description': 'Monitores e telas.', 'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]
    st.session_state.db_competitors = pd.DataFrame(mock_initial_competitors)

if 'db_quotes' not in st.session_state: 
    mock_initial_quotes = [
        {'id': 1, 'item_id': 101, 'supplier_id': 1, 'price': 7500.00, 'notes': 'Garantia 1 ano', 'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': 2, 'item_id': 102, 'supplier_id': 1, 'price': 800.00, 'notes': '', 'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]
    st.session_state.db_quotes = pd.DataFrame(mock_initial_quotes)

if 'db_bids' not in st.session_state: 
    mock_initial_bids = [
        {'id': 1, 'item_id': 101, 'competitor_id': 1, 'price': 7100.00, 'timestamp': pd.to_datetime('2025-05-28 10:00:00'), 'notes': 'Lance inicial', 'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]
    st.session_state.db_bids = pd.DataFrame(mock_initial_bids)
    st.session_state.db_bids['timestamp'] = pd.to_datetime(st.session_state.db_bids['timestamp'])


# Próximos IDs
if 'next_bidding_id' not in st.session_state: st.session_state.next_bidding_id = (st.session_state.db_biddings['id'].max() + 1) if not st.session_state.db_biddings.empty else 1
if 'next_item_id' not in st.session_state: st.session_state.next_item_id = (st.session_state.db_items['id'].max() + 1) if not st.session_state.db_items.empty else 101
if 'next_supplier_id' not in st.session_state: st.session_state.next_supplier_id = (st.session_state.db_suppliers['id'].max() + 1) if not st.session_state.db_suppliers.empty else 1
if 'next_competitor_id' not in st.session_state: st.session_state.next_competitor_id = (st.session_state.db_competitors['id'].max() + 1) if not st.session_state.db_competitors.empty else 1
if 'next_quote_id' not in st.session_state: st.session_state.next_quote_id = (st.session_state.db_quotes['id'].max() + 1) if not st.session_state.db_quotes.empty else 1
if 'next_bid_id' not in st.session_state: st.session_state.next_bid_id = (st.session_state.db_bids['id'].max() + 1) if not st.session_state.db_bids.empty else 1

# Estado para controlar abertura de diálogos e edição
for dialog_type in ['bidding', 'item', 'supplier', 'competitor']:
    if f'show_manage_{dialog_type}_dialog' not in st.session_state: st.session_state[f'show_manage_{dialog_type}_dialog'] = False
    if f'editing_{dialog_type}_id' not in st.session_state: st.session_state[f'editing_{dialog_type}_id'] = None
    if f'confirm_delete_{dialog_type}' not in st.session_state: st.session_state[f'confirm_delete_{dialog_type}'] = False

if 'parent_bidding_id_for_item_dialog' not in st.session_state: st.session_state.parent_bidding_id_for_item_dialog = None


# --- Funções Auxiliares para Gráficos ---
def create_quotes_figure(quotes_df_display: pd.DataFrame) -> go.Figure:
    fig = px.bar(quotes_df_display, x='supplier_name', y='price', title="Comparativo de Preços dos Orçamentos", labels={'supplier_name': 'Fornecedor', 'price': 'Preço (R$)'}, color='supplier_name', text_auto=True)
    fig.update_layout(xaxis_title="Fornecedor", yaxis_title="Preço (R$)", legend_title_text='Fornecedores', dragmode='pan')
    return fig

def create_bids_figure(bids_df_display: pd.DataFrame, min_quote_price: float = None) -> go.Figure:
    if 'timestamp' in bids_df_display.columns and not bids_df_display['timestamp'].isnull().all():
        b_df_sorted = bids_df_display.sort_values(by='timestamp') if len(bids_df_display) > 1 else bids_df_display
        fig = px.line(b_df_sorted, x='timestamp', y='price', color='competitor_name', title="Evolução dos Lances ao Longo do Tempo", labels={'timestamp': 'Momento do Lance', 'price': 'Preço do Lance (R$)', 'competitor_name': 'Concorrente'}, markers=True)
    else: 
        fig = px.bar(bids_df_display, x='competitor_name', y='price', title="Comparativo de Preços dos Lances (sem timestamp)", labels={'competitor_name': 'Concorrente', 'price': 'Preço do Lance (R$)'}, color='competitor_name', text_auto=True)
    fig.update_layout(dragmode='pan', legend_title_text='Concorrentes') 
    if min_quote_price is not None:
        fig.add_hline(y=min_quote_price, line_dash="dash", line_color="red", annotation_text=f"Menor Orçamento: R${min_quote_price:,.2f}", annotation_position="bottom right", annotation_font_size=10, annotation_font_color="red")
    return fig

# --- Funções de Diálogo Genéricas (CRUD) ---
def _manage_generic_dialog(
    entity_type: str, db_key: str, next_id_key: str, 
    form_fields_config: dict, title_singular: str, 
    related_entities_to_delete: list = None,
    parent_id_field_name: str = None, 
    parent_id_value: any = None      
    ):
    data = {field: config.get('default', '') for field, config in form_fields_config.items() if isinstance(config, dict)}
    dialog_mode = "new"
    editing_id_key = f'editing_{entity_type}_id'
    show_dialog_key = f'show_manage_{entity_type}_dialog'
    confirm_delete_key = f'confirm_delete_{entity_type}'

    if st.session_state[editing_id_key] is not None:
        try:
            entity_to_edit_series = st.session_state[db_key][st.session_state[db_key]['id'] == st.session_state[editing_id_key]].iloc[0]
            for field in form_fields_config.keys():
                if field in entity_to_edit_series: data[field] = entity_to_edit_series[field]
            data['id'] = entity_to_edit_series['id'] 
            dialog_mode = "edit"
        except IndexError:
            st.error(f"{title_singular} não encontrado(a) para edição."); st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun(); return

    st.subheader(f"{'Editar' if dialog_mode == 'edit' else f'Novo(a)'} {title_singular}" + (f" (ID: {st.session_state[editing_id_key]})" if dialog_mode == 'edit' else ""))

    with st.form(key=f"{entity_type}_form"):
        form_data_submitted = {}
        for field, config in form_fields_config.items():
            if not isinstance(config, dict): continue
            field_label = config.get('label', field.replace('_', ' ').title())
            current_field_value = data.get(field, config.get('default', ''))

            if config['type'] == 'text_input': form_data_submitted[field] = st.text_input(field_label, value=current_field_value)
            elif config['type'] == 'selectbox':
                options = config.get('options', [])
                index = options.index(current_field_value) if current_field_value in options else 0
                form_data_submitted[field] = st.selectbox(field_label, options=options, index=index)
            elif config['type'] == 'date_input':
                 val = current_field_value
                 if pd.isna(val) or val is None: val = None
                 elif isinstance(val, str): val = pd.to_datetime(val, errors='coerce').date()
                 elif isinstance(val, datetime): val = val.date()
                 form_data_submitted[field] = st.date_input(field_label, value=val)
            elif config['type'] == 'time_input':
                val = current_field_value
                if pd.isna(val) or val is None: val = None
                elif isinstance(val, str):
                    try: val = datetime.strptime(val, '%H:%M:%S').time()
                    except ValueError: val = None
                form_data_submitted[field] = st.time_input(field_label, value=val if isinstance(val, time) else None)
            elif config['type'] == 'text_area': form_data_submitted[field] = st.text_area(field_label, value=current_field_value)
            elif config['type'] == 'number_input': form_data_submitted[field] = st.number_input(field_label, value=current_field_value, min_value=config.get('min_value'), step=config.get('step',1), format=config.get('format'))
        
        form_action_cols = st.columns(2) 
        with form_action_cols[0]:
            submitted = st.form_submit_button(f"💾 Salvar {title_singular}" if dialog_mode == "new" else f"💾 Atualizar {title_singular}", use_container_width=True)
        if dialog_mode == "edit":
            with form_action_cols[1]:
                if st.form_submit_button(f"🗑️ Deletar {title_singular}", type="secondary", use_container_width=True):
                    st.session_state[confirm_delete_key] = True
        
        if submitted:
            is_valid = all(not (config.get('required') and not form_data_submitted.get(field) and form_data_submitted.get(field) != 0) for field, config in form_fields_config.items())
            if not is_valid: st.error("Por favor, preencha todos os campos obrigatórios (*).")
            else:
                current_time = datetime.now()
                save_data = {k: v for k, v in form_data_submitted.items() if k in form_fields_config} 
                save_data['updated_at'] = current_time

                if dialog_mode == "new":
                    save_data['id'] = st.session_state[next_id_key]
                    save_data['created_at'] = current_time
                    if parent_id_field_name and parent_id_value is not None: save_data[parent_id_field_name] = parent_id_value
                    st.session_state[db_key] = pd.concat([st.session_state[db_key], pd.DataFrame([save_data])], ignore_index=True)
                    st.session_state[next_id_key] += 1
                    st.success(f"{title_singular} '{save_data.get('name', save_data.get('process_number', ''))}' criado(a) com sucesso!")
                else: 
                    idx = st.session_state[db_key][st.session_state[db_key]['id'] == st.session_state[editing_id_key]].index
                    for key_update, value_update in save_data.items():
                        st.session_state[db_key].loc[idx, key_update] = value_update
                    st.success(f"{title_singular} '{save_data.get('name', save_data.get('process_number', ''))}' atualizado(a) com sucesso!")
                
                st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun()

    if st.session_state.get(confirm_delete_key, False):
        entity_name_display = data.get('name', data.get('process_number', ''))
        warning_message = f"Tem certeza que deseja deletar {title_singular.lower()} '{entity_name_display}'?"
        if related_entities_to_delete: warning_message += f" Todas as {', '.join(related_entities_to_delete)} associadas também serão deletadas. Esta ação não pode ser desfeita."
        st.warning(warning_message)
        confirm_cols_del = st.columns(2)
        if confirm_cols_del[0].button(f"🔴 Confirmar Exclusão", type="primary", key=f"confirm_del_btn_{entity_type}", use_container_width=True):
            editing_id_val = st.session_state[editing_id_key]
            if entity_type == 'bidding':
                items_of_bidding_ids = st.session_state.db_items[st.session_state.db_items['bidding_id'] == editing_id_val]['id'].tolist()
                if items_of_bidding_ids:
                    st.session_state.db_quotes = st.session_state.db_quotes[~st.session_state.db_quotes['item_id'].isin(items_of_bidding_ids)]
                    st.session_state.db_bids = st.session_state.db_bids[~st.session_state.db_bids['item_id'].isin(items_of_bidding_ids)]
                st.session_state.db_items = st.session_state.db_items[st.session_state.db_items['bidding_id'] != editing_id_val]
            elif entity_type == 'item':
                st.session_state.db_quotes = st.session_state.db_quotes[st.session_state.db_quotes['item_id'] != editing_id_val]
                st.session_state.db_bids = st.session_state.db_bids[st.session_state.db_bids['item_id'] != editing_id_val]
            elif entity_type == 'supplier': st.session_state.db_quotes = st.session_state.db_quotes[st.session_state.db_quotes['supplier_id'] != editing_id_val]
            elif entity_type == 'competitor': st.session_state.db_bids = st.session_state.db_bids[st.session_state.db_bids['competitor_id'] != editing_id_val]

            st.session_state[db_key] = st.session_state[db_key][st.session_state[db_key]['id'] != editing_id_val]
            st.success(f"{title_singular} '{entity_name_display}' e suas dependências foram deletados(as).")
            
            if st.session_state.get(f'selected_{entity_type}_id') == editing_id_val: st.session_state[f'selected_{entity_type}_id'] = None
            if entity_type == 'bidding': st.session_state.selected_bidding_id = None; st.session_state.selected_item_id = None 
            if entity_type == 'item' and st.session_state.selected_item_id == editing_id_val: st.session_state.selected_item_id = None

            st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.session_state[confirm_delete_key] = False; st.rerun()
        if confirm_cols_del[1].button("Cancelar", key=f"cancel_del_btn_{entity_type}", use_container_width=True):
            st.session_state[confirm_delete_key] = False; st.rerun()

    if st.button(f"Fechar Diálogo", key=f"close_dialog_btn_{entity_type}", use_container_width=True): 
        st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.session_state[confirm_delete_key] = False; st.rerun()

# --- Definições de Configuração dos Formulários ---
bidding_form_config = {
    'process_number': {'label': 'Nº do Processo*', 'type': 'text_input', 'required': True},
    'city': {'label': 'Cidade*', 'type': 'text_input', 'required': True},
    'mode': {'label': 'Modalidade*', 'type': 'selectbox', 'options': ["Pregão Eletrônico", "Pregão Presencial", "Tomada de Preços", "Concorrência Pública", "Convite", "Leilão"], 'required': True, 'default': "Pregão Eletrônico"},
    'session_date': {'label': 'Data da Sessão (Opcional)', 'type': 'date_input', 'default': None},
    'session_time': {'label': 'Hora da Sessão (Opcional)', 'type': 'time_input', 'default': None}
}
item_form_config = {
    'name': {'label': 'Nome do Item*', 'type': 'text_input', 'required': True},
    'description': {'label': 'Descrição', 'type': 'text_area', 'default': ''},
    'quantity': {'label': 'Quantidade*', 'type': 'number_input', 'min_value': 1, 'default': 1, 'required': True, 'step': 1},
    'unit': {'label': 'Unidade*', 'type': 'text_input', 'default': 'UN', 'required': True}
}
contact_entity_form_config = {
    'name': {'label': 'Nome*', 'type': 'text_input', 'required': True},
    'website': {'label': 'Website', 'type': 'text_input', 'default': ''},
    'email': {'label': 'Email', 'type': 'text_input', 'default': ''},
    'phone': {'label': 'Telefone', 'type': 'text_input', 'default': ''},
    'description': {'label': 'Descrição/Observações', 'type': 'text_area', 'default': ''}
}

# --- Funções Wrapper para Diálogos Específicos ---
@st.dialog("Gerenciar Licitação", width="large")
def manage_bidding_dialog_wrapper():
    _manage_generic_dialog('bidding', 'db_biddings', 'next_bidding_id', bidding_form_config, "Licitação", related_entities_to_delete=["itens", "orçamentos dos itens", "lances dos itens"])

@st.dialog("Gerenciar Item da Licitação", width="large")
def manage_item_dialog_wrapper():
    parent_bidding_id = st.session_state.parent_bidding_id_for_item_dialog
    if parent_bidding_id is None: st.error("Licitação pai não definida."); st.session_state.show_manage_item_dialog = False; st.rerun(); return
    try:
        parent_bidding_info = st.session_state.db_biddings[st.session_state.db_biddings['id'] == parent_bidding_id].iloc[0]
        st.info(f"Para Licitação: {parent_bidding_info['process_number']} - {parent_bidding_info['city']}")
    except IndexError: st.error("Licitação pai não encontrada."); st.session_state.show_manage_item_dialog = False; st.rerun(); return
    _manage_generic_dialog('item', 'db_items', 'next_item_id', item_form_config, "Item", related_entities_to_delete=["orçamentos", "lances"], parent_id_field_name='bidding_id', parent_id_value=parent_bidding_id)

@st.dialog("Gerenciar Fornecedor", width="large")
def manage_supplier_dialog_wrapper():
    _manage_generic_dialog('supplier', 'db_suppliers', 'next_supplier_id', contact_entity_form_config, "Fornecedor", related_entities_to_delete=["orçamentos"])

@st.dialog("Gerenciar Concorrente", width="large")
def manage_competitor_dialog_wrapper():
    _manage_generic_dialog('competitor', 'db_competitors', 'next_competitor_id', contact_entity_form_config, "Concorrente", related_entities_to_delete=["lances"])

# --- Funções Auxiliares para Selectbox ---
def get_options_map(db_key: str = None, df_input: pd.DataFrame = None, name_col: str = 'name', extra_cols: list = None, default_message:str = "Selecione...") -> tuple:
    current_df = None
    if df_input is not None: 
        current_df = df_input.copy() # Use a copy to avoid modifying the original DataFrame
    elif db_key is not None:
        current_df = st.session_state.get(db_key, pd.DataFrame()).copy()
    else: 
        current_df = pd.DataFrame()

    if current_df.empty: 
        return {None: default_message}, [None]
    
    options_map = {None: default_message}
    ids_list = [None]

    if extra_cols: 
        if all(col in current_df.columns for col in extra_cols):
            current_df['display_name'] = current_df[extra_cols[0]].astype(str) + " - " + current_df[extra_cols[1]].astype(str) + " (" + current_df[extra_cols[2]].astype(str) + ")"
            options_map.update({row['id']: row['display_name'] for _, row in current_df.iterrows()})
            ids_list.extend(current_df['id'].tolist())
        else: 
            options_map.update({row['id']: str(row['id']) for _, row in current_df.iterrows()}) # Fallback
            ids_list.extend(current_df['id'].tolist())
    elif name_col in current_df.columns: 
        options_map.update({row['id']: row[name_col] for _, row in current_df.iterrows()})
        ids_list.extend(current_df['id'].tolist())
    else: 
        options_map.update({row['id']: str(row['id']) for _, row in current_df.iterrows()}) # Fallback
        ids_list.extend(current_df['id'].tolist())
        
    return options_map, ids_list


# --- Página Principal da Aplicação ---
st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom") 
bidding_options_map, bidding_option_ids = get_options_map(db_key='db_biddings', extra_cols=['process_number', 'city', 'mode'], default_message=DEFAULT_BIDDING_SELECT_MESSAGE)

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
items_df_for_select = pd.DataFrame() 
if st.session_state.selected_bidding_id is not None:
    col_item_select, col_item_manage_btn = st.columns([5, 2], vertical_alignment="bottom")
    
    items_df_for_select = st.session_state.db_items[st.session_state.db_items['bidding_id'] == st.session_state.selected_bidding_id]
    item_options_map, item_option_ids = get_options_map(df_input=items_df_for_select, name_col='name', default_message=DEFAULT_ITEM_SELECT_MESSAGE) 

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
        if not items_df_for_select.empty: 
            current_item_details_series = items_df_for_select[items_df_for_select['id'] == st.session_state.selected_item_id]
            if not current_item_details_series.empty:
                current_item_details = current_item_details_series.iloc[0]
                st.markdown(f"**Item Selecionado:** {current_item_details['name']} (ID: {st.session_state.selected_item_id})")
                st.markdown(f"**Descrição:** {current_item_details['description']}")
                st.markdown(f"**Quantidade:** {current_item_details['quantity']} {current_item_details['unit']}")
                st.markdown("---")

                expander_cols = st.columns(2)
                with expander_cols[0]:
                    with st.expander(f"➕ Adicionar Novo Orçamento para {current_item_details['name']}", expanded=False):
                        col_supp_select, col_supp_manage = st.columns([3,2], vertical_alignment="bottom")
                        supplier_options_map, supplier_option_ids = get_options_map(db_key='db_suppliers', default_message=DEFAULT_SUPPLIER_SELECT_MESSAGE)
                        with col_supp_select:
                            selected_supplier_id_quote = st.selectbox("Fornecedor*:", options=supplier_option_ids, format_func=lambda x: supplier_options_map.get(x, DEFAULT_SUPPLIER_SELECT_MESSAGE), key="sb_supplier_quote_exp")
                        with col_supp_manage:
                            if st.button("👤 Ger. Fornecedores", key="btn_manage_suppliers_quote_exp", use_container_width=True):
                                st.session_state.editing_supplier_id = selected_supplier_id_quote 
                                st.session_state.show_manage_supplier_dialog = True
                        with st.form(key="new_quote_form"):
                            quote_price = st.number_input("Preço do Orçamento*", min_value=0.01, format="%.2f", key="quote_price_input_exp")
                            quote_notes = st.text_area("Notas do Orçamento", key="quote_notes_input_exp")
                            if st.form_submit_button("💾 Salvar Orçamento"):
                                if selected_supplier_id_quote and quote_price > 0:
                                    current_time = datetime.now()
                                    new_quote_data = {'id': st.session_state.next_quote_id, 'item_id': st.session_state.selected_item_id, 'supplier_id': selected_supplier_id_quote, 'price': quote_price, 'notes': quote_notes, 'created_at': current_time, 'updated_at': current_time}
                                    st.session_state.db_quotes = pd.concat([st.session_state.db_quotes, pd.DataFrame([new_quote_data])], ignore_index=True); st.session_state.next_quote_id += 1
                                    st.success("Orçamento adicionado!"); st.rerun()
                                else: st.error("Selecione um fornecedor e insira um preço válido.")
                with expander_cols[1]:
                    with st.expander(f"➕ Adicionar Novo Lance para {current_item_details['name']}", expanded=False):
                        col_comp_select, col_comp_manage = st.columns([3,2], vertical_alignment="bottom")
                        competitor_options_map, competitor_option_ids = get_options_map(db_key='db_competitors', default_message=DEFAULT_COMPETITOR_SELECT_MESSAGE)
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
                                if selected_competitor_id_bid and bid_price > 0:
                                    current_time = datetime.now()
                                    new_bid_data = {'id': st.session_state.next_bid_id, 'item_id': st.session_state.selected_item_id, 'competitor_id': selected_competitor_id_bid, 'price': bid_price, 'notes': bid_notes, 'timestamp': current_time, 'created_at': current_time, 'updated_at': current_time}
                                    st.session_state.db_bids = pd.concat([st.session_state.db_bids, pd.DataFrame([new_bid_data])], ignore_index=True); st.session_state.next_bid_id += 1
                                    st.success("Lance adicionado!"); st.rerun()
                                else: st.error("Selecione um concorrente e insira um preço válido.")

                quotes_for_item_df_display = st.session_state.db_quotes[st.session_state.db_quotes['item_id'] == st.session_state.selected_item_id].copy()
                bids_for_item_df_display = st.session_state.db_bids[st.session_state.db_bids['item_id'] == st.session_state.selected_item_id].copy()
                if not quotes_for_item_df_display.empty and not st.session_state.db_suppliers.empty: quotes_for_item_df_display = pd.merge(quotes_for_item_df_display, st.session_state.db_suppliers[['id', 'name']], left_on='supplier_id', right_on='id', how='left').rename(columns={'name': 'supplier_name'})
                if not bids_for_item_df_display.empty and not st.session_state.db_competitors.empty: bids_for_item_df_display = pd.merge(bids_for_item_df_display, st.session_state.db_competitors[['id', 'name']], left_on='competitor_id', right_on='id', how='left').rename(columns={'name': 'competitor_name'})

                table_cols_display = st.columns(2) 
                with table_cols_display[0]:
                    st.markdown("##### Orçamentos Recebidos")
                    if not quotes_for_item_df_display.empty: st.dataframe(quotes_for_item_df_display[['supplier_name', 'price', 'notes', 'updated_at']], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum orçamento cadastrado para este item.")
                with table_cols_display[1]:
                    st.markdown("##### Lances Recebidos")
                    if not bids_for_item_df_display.empty:
                        bids_to_show = bids_for_item_df_display.copy(); 
                        if 'timestamp' in bids_to_show.columns: bids_to_show['timestamp'] = pd.to_datetime(bids_to_show['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        st.dataframe(bids_to_show[['competitor_name', 'price', 'timestamp', 'notes', 'updated_at']], hide_index=True, use_container_width=True)
                    else: st.info("Nenhum lance cadastrado para este item.")

                st.markdown("---"); st.subheader("Gráficos do Item")
                graph_cols_display = st.columns(2) 
                with graph_cols_display[0]:
                    if not quotes_for_item_df_display.empty: st.plotly_chart(create_quotes_figure(quotes_for_item_df_display), use_container_width=True)
                    else: st.caption("Gráfico de orçamentos não disponível.")
                with graph_cols_display[1]:
                    if not bids_for_item_df_display.empty and 'price' in bids_for_item_df_display.columns:
                        min_quote_price_val = quotes_for_item_df_display['price'].min() if not quotes_for_item_df_display.empty and 'price' in quotes_for_item_df_display.columns else None
                        st.plotly_chart(create_bids_figure(bids_for_item_df_display, min_quote_price_val), use_container_width=True)
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
if st.session_state.get('show_manage_supplier_dialog', False): manage_supplier_dialog_wrapper()
if st.session_state.get('show_manage_competitor_dialog', False): manage_competitor_dialog_wrapper()

