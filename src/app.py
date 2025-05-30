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
    if 'created_at' in bids_df_display.columns and not bids_df_display['created_at'].isnull().all():
        b_df_sorted = bids_df_display.sort_values(by='created_at') if len(bids_df_display) > 1 else bids_df_display
        fig = px.line(b_df_sorted, x='created_at', y='price', color='competitor_name', title="Evolução dos Lances ao Longo do Tempo", labels={'created_at': 'Momento do Lance', 'price': 'Preço do Lance (R$)', 'competitor_name': 'Concorrente'}, markers=True)
    else: 
        fig = px.bar(bids_df_display, x='competitor_name', y='price', title="Comparativo de Preços dos Lances (sem timestamp)", labels={'competitor_name': 'Concorrente', 'price': 'Preço do Lance (R$)'}, color='competitor_name', text_auto=True)
    fig.update_layout(dragmode='pan', legend_title_text='Concorrentes') 
    if min_quote_price is not None:
        fig.add_hline(y=min_quote_price, line_dash="dash", line_color="red", annotation_text=f"Menor Orçamento: R${min_quote_price:,.2f}", annotation_position="bottom right", annotation_font_size=10, annotation_font_color="red")
    return fig

# --- Funções de Diálogo Genéricas (CRUD) ---
def _manage_generic_dialog(
    entity_type: str, repo: SQLModelRepository,
    form_fields_config: dict, title_singular: str, 
    related_entities_to_delete: list = None, # This will need adjustment for DB cascade deletes later
    parent_id_field_name: str = None, 
    parent_id_value: any = None      
    ):
    data = {field: config.get('default', '') for field, config in form_fields_config.items() if isinstance(config, dict)}
    dialog_mode = "new"
    editing_id_key = f'editing_{entity_type}_id'
    # db_key is no longer used directly for fetching, repo is used.
    # next_id_key is no longer used.
    show_dialog_key = f'show_manage_{entity_type}_dialog'
    confirm_delete_key = f'confirm_delete_{entity_type}'

    if st.session_state[editing_id_key] is not None:
        try:
            # Fetch entity from DB for editing
            entity_to_edit = repo.get(st.session_state[editing_id_key]) # Changed get_by_id to get
            if not entity_to_edit:
                st.error(f"{title_singular} não encontrado(a) para edição (ID: {st.session_state[editing_id_key]})."); st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun(); return

            # Populate form data from the fetched entity
            if entity_to_edit: # Ensure entity_to_edit is not None
                for field_key, config_val in form_fields_config.items(): # Use items() for better access
                    if isinstance(config_val, dict): # Check if it's a field config
                        model_attr = field_key
                        if entity_type == "item" and field_key == "description":
                            model_attr = "desc"

                        if hasattr(entity_to_edit, model_attr):
                            data[field_key] = getattr(entity_to_edit, model_attr)
                        elif 'default' in config_val: # Fallback to default if attr not present
                             data[field_key] = config_val['default']
                        else:
                             data[field_key] = '' # Or some other suitable default
                data['id'] = entity_to_edit.id
            dialog_mode = "edit"
        except Exception as e: # Catch potential errors during DB fetch or attribute access
            st.error(f"Erro ao carregar {title_singular} para edição: {e}"); st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun(); return

    st.subheader(f"{'Editar' if dialog_mode == 'edit' else f'Novo(a)'} {title_singular}" + (f" (ID: {data.get('id')})" if dialog_mode == 'edit' else ""))

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

                if entity_type == "item" and "description" in save_data:
                    save_data["desc"] = save_data.pop("description")

                # Handle date/time conversions that might be strings from form
                for field, config in form_fields_config.items():
                    if config['type'] == 'date_input' and isinstance(save_data.get(field), str):
                        save_data[field] = pd.to_datetime(save_data[field], errors='coerce').date() if save_data.get(field) else None
                    elif config['type'] == 'time_input' and isinstance(save_data.get(field), str):
                        try:
                            save_data[field] = datetime.strptime(save_data[field], '%H:%M:%S').time() if save_data.get(field) else None
                        except ValueError:
                            save_data[field] = None # Or handle error appropriately

                if dialog_mode == "new":
                    save_data['created_at'] = current_time # Model default might also handle this
                    save_data['updated_at'] = current_time # Model default might also handle this
                    if parent_id_field_name and parent_id_value is not None:
                        save_data[parent_id_field_name] = parent_id_value

                    # Remove 'id' if present, as DB will generate it
                    if 'id' in save_data: del save_data['id']

                    try:
                        new_entity = repo.model(**save_data)
                        created_entity = repo.add(new_entity)
                        # Fetch the name or process_number for the success message
                        display_name = created_entity.name if hasattr(created_entity, 'name') else getattr(created_entity, 'process_number', '')
                        st.success(f"{title_singular} '{display_name}' (ID: {created_entity.id}) criado(a) com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao criar {title_singular}: {e}")
                        st.session_state[show_dialog_key] = True # Keep dialog open on error
                        st.rerun(); return

                else: # dialog_mode == "edit"
                    entity_id_to_update = st.session_state[editing_id_key]
                    save_data['updated_at'] = current_time
                    try:
                        updated_entity = repo.update(entity_id_to_update, save_data)
                        display_name = updated_entity.name if hasattr(updated_entity, 'name') else getattr(updated_entity, 'process_number', '')
                        st.success(f"{title_singular} '{display_name}' (ID: {updated_entity.id}) atualizado(a) com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao atualizar {title_singular}: {e}")
                        st.session_state[show_dialog_key] = True # Keep dialog open on error
                        st.rerun(); return
                
                st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun()

    if st.session_state.get(confirm_delete_key, False):
        entity_name_display = data.get('name', data.get('process_number', ''))
        warning_message = f"Tem certeza que deseja deletar {title_singular.lower()} '{entity_name_display}'?"
        if related_entities_to_delete: warning_message += f" Todas as {', '.join(related_entities_to_delete)} associadas também serão deletadas. Esta ação não pode ser desfeita."
        st.warning(warning_message)
        confirm_cols_del = st.columns(2)
        if confirm_cols_del[0].button(f"🔴 Confirmar Exclusão", type="primary", key=f"confirm_del_btn_{entity_type}", use_container_width=True):
            editing_id_val = st.session_state[editing_id_key]
            try:
                if entity_type == 'bidding':
                    all_items = item_repo.get_all() or []
                    items_to_delete = [item for item in all_items if item.bidding_id == editing_id_val]
                    for item_del in items_to_delete:
                        all_quotes = quote_repo.get_all() or []
                        quotes_to_delete = [q for q in all_quotes if q.item_id == item_del.id]
                        for quote_del in quotes_to_delete:
                            quote_repo.delete(quote_del.id)

                        all_bids = bid_repo.get_all() or []
                        bids_to_delete = [b for b in all_bids if b.item_id == item_del.id]
                        for bid_del in bids_to_delete:
                            bid_repo.delete(bid_del.id)
                        item_repo.delete(item_del.id)

                elif entity_type == 'item':
                    item_id_to_delete = editing_id_val
                    all_quotes = quote_repo.get_all() or []
                    quotes_to_delete = [q for q in all_quotes if q.item_id == item_id_to_delete]
                    for quote_del in quotes_to_delete:
                        quote_repo.delete(quote_del.id)

                    all_bids = bid_repo.get_all() or []
                    bids_to_delete = [b for b in all_bids if b.item_id == item_id_to_delete]
                    for bid_del in bids_to_delete:
                        bid_repo.delete(bid_del.id)

                elif entity_type == 'supplier':
                    supplier_id_to_delete = editing_id_val
                    all_quotes = quote_repo.get_all() or []
                    quotes_to_delete = [q for q in all_quotes if q.supplier_id == supplier_id_to_delete]
                    for quote_del in quotes_to_delete:
                        quote_repo.delete(quote_del.id)

                elif entity_type == 'competitor':
                    competitor_id_to_delete = editing_id_val
                    all_bids = bid_repo.get_all() or []
                    bids_to_delete = [b for b in all_bids if b.competitor_id == competitor_id_to_delete]
                    for bid_del in bids_to_delete:
                        bid_repo.delete(bid_del.id)

                # Finally, delete the main entity itself
                repo.delete(editing_id_val)
                st.success(f"{title_singular} '{entity_name_display}' e suas dependências foram deletados(as) com sucesso.")

            except Exception as e:
                st.error(f"Erro ao deletar {title_singular} e/ou suas dependências: {e}")
                st.session_state[show_dialog_key] = True # Keep dialog open
                st.rerun(); return

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
    _manage_generic_dialog('bidding', bidding_repo, bidding_form_config, "Licitação", related_entities_to_delete=["itens", "orçamentos dos itens", "lances dos itens"])

@st.dialog("Gerenciar Item da Licitação", width="large")
def manage_item_dialog_wrapper():
    parent_bidding_id = st.session_state.parent_bidding_id_for_item_dialog
    if parent_bidding_id is None: st.error("Licitação pai não definida."); st.session_state.show_manage_item_dialog = False; st.rerun(); return

    parent_bidding = bidding_repo.get(parent_bidding_id) # Changed get_by_id to get
    if not parent_bidding:
        st.error("Licitação pai não encontrada."); st.session_state.show_manage_item_dialog = False; st.rerun(); return
    st.info(f"Para Licitação: {parent_bidding.process_number} - {parent_bidding.city}")

    _manage_generic_dialog('item', item_repo, item_form_config, "Item", related_entities_to_delete=["orçamentos", "lances"], parent_id_field_name='bidding_id', parent_id_value=parent_bidding_id)

@st.dialog("Gerenciar Fornecedor", width="large")
def manage_supplier_dialog_wrapper():
    _manage_generic_dialog('supplier', supplier_repo, contact_entity_form_config, "Fornecedor", related_entities_to_delete=["orçamentos"])

@st.dialog("Gerenciar Concorrente", width="large")
def manage_competitor_dialog_wrapper():
    _manage_generic_dialog('competitor', competitor_repo, contact_entity_form_config, "Concorrente", related_entities_to_delete=["lances"])

# --- Funções Auxiliares para Selectbox ---
def get_options_map(data_list: list, name_col: str = 'name', extra_cols: list = None, default_message:str = "Selecione...") -> tuple:
    if not data_list:
        return {None: default_message}, [None]

    options_map = {None: default_message}
    ids_list = [None]

    for row in data_list:
        if extra_cols:
            try:
                # Ensure all extra_cols exist as attributes
                display_name_parts = [str(getattr(row, col)) for col in extra_cols]
                display_name = " - ".join(display_name_parts[:2]) # First two parts
                if len(extra_cols) > 2:
                    display_name += f" ({display_name_parts[2]})" # Third part in parentheses
                options_map[row.id] = display_name
            except AttributeError:
                # Fallback if an attribute is missing
                options_map[row.id] = str(row.id)
        elif hasattr(row, name_col):
            options_map[row.id] = getattr(row, name_col)
        else:
            # Fallback if name_col attribute is missing
            options_map[row.id] = str(row.id)
        ids_list.append(row.id)
        
    return options_map, ids_list


# --- Página Principal da Aplicação ---
st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

# --- Seleção de Licitação e Botão de Gerenciamento ---
col_bid_select, col_bid_manage_btn = st.columns([5, 2], vertical_alignment="bottom") 
all_biddings = bidding_repo.get_all()
if all_biddings is None: all_biddings = [] # Handle case where get_all might return None
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
                        # TODO: Update this get_options_map call for suppliers
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

