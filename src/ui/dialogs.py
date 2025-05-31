import streamlit as st
import pandas as pd
from datetime import datetime, time, date # Ensure date is also imported
from typing import Any, TypedDict, Literal, Union # Added TypedDict, Literal, Union
from collections.abc import Callable

# Assuming repository instances are defined in app.py or a similar accessible module
# This will likely need adjustment in a later step to avoid circular dependencies
# For now, we'll add placeholders and assume they can be imported.
# from app import bidding_repo, item_repo, supplier_repo, competitor_repo, quote_repo, bid_repo
# from db.models import Quote, Bid, Bidding, Item, Supplier, Competitor # BiddingMode is not directly used here but Bidding is

# Placeholder imports: these will be resolved when app.py is refactored
# For the purpose of this step, we assume these can be imported.
# If not, they would need to be passed as arguments.
from repository import SQLModelRepository # This is a generic type, not an instance
from db.models import BiddingMode, Bidding, Item, Supplier, Competitor, Quote, Bid # Added import

# --- Type Aliases for Form Configuration ---
class FormFieldConfigBase(TypedDict, total=False):
    label: str
    required: bool
    default: Any

class TextFieldConfig(FormFieldConfigBase):
    type: Literal["text_input", "text_area"]

class NumberFieldConfig(FormFieldConfigBase):
    type: Literal["number_input"]
    min_value: float | int
    step: float | int
    format: str

class SelectFieldConfig(FormFieldConfigBase):
    type: Literal["selectbox"]
    options: list[Any]
    format_func: Callable[[Any], str]

class DateFieldConfig(FormFieldConfigBase):
    type: Literal["date_input"]

class TimeFieldConfig(FormFieldConfigBase):
    type: Literal["time_input"]

FormFieldConfig = Union[
    TextFieldConfig,
    NumberFieldConfig,
    SelectFieldConfig,
    DateFieldConfig,
    TimeFieldConfig,
]

FormConfig = dict[str, FormFieldConfig]


# --- Definições de Configuração dos Formulários ---
bidding_form_config: FormConfig = {
    'process_number': {'label': 'Nº do Processo*', 'type': 'text_input', 'required': True},
    'city': {'label': 'Cidade*', 'type': 'text_input', 'required': True},
    'mode': {
        'label': 'Modalidade*',
        'type': 'selectbox',
        'options': list(BiddingMode),
        'required': True,
        'default': BiddingMode.PE,
        'format_func': lambda mode: mode.value
    },
    'session_date': {'label': 'Data da Sessão (Opcional)', 'type': 'date_input', 'default': None},
    'session_time': {'label': 'Hora da Sessão (Opcional)', 'type': 'time_input', 'default': None}
}
item_form_config: FormConfig = {
    'name': {'label': 'Nome do Item*', 'type': 'text_input', 'required': True},
    'description': {'label': 'Descrição', 'type': 'text_area', 'default': ''},
    'quantity': {'label': 'Quantidade*', 'type': 'number_input', 'min_value': 1.0, 'default': 1.0, 'required': True, 'step': 1.0, 'format': "%.2f"}, # Added format for consistency
    'unit': {'label': 'Unidade*', 'type': 'text_input', 'default': 'UN', 'required': True}
}
contact_entity_form_config: FormConfig = {
    'name': {'label': 'Nome*', 'type': 'text_input', 'required': True},
    'website': {'label': 'Website', 'type': 'text_input', 'default': ''},
    'email': {'label': 'Email', 'type': 'text_input', 'default': ''},
    'phone': {'label': 'Telefone', 'type': 'text_input', 'default': ''},
    'description': {'label': 'Descrição/Observações', 'type': 'text_area', 'default': ''}
}

# --- Helper Functions for _manage_generic_dialog ---

def _render_form_fields(
    form_fields_config: FormConfig,
    current_data: dict[str, Any]
) -> dict[str, Any]:
    """Renders form fields based on configuration and current data."""
    form_data_submitted: dict[str, Any] = {}
    for field, config in form_fields_config.items():
        # Since FormFieldConfig is a Union, config will be one of the TypedDicts
        # All TypedDicts here inherit 'label' and 'default' (optional) from FormFieldConfigBase
        # However, direct access like config.get('label') is problematic for Unions if keys are not common to all members in a way type checker understands
        # For this step, we'll keep it as is, but a more robust way would be to check config['type'] first.

        field_label = config.get('label', field.replace('_', ' ').title()) # type: ignore
        current_field_value = current_data.get(field, config.get('default')) # type: ignore

        field_type = config['type']

        if field_type == 'text_input':
            form_data_submitted[field] = st.text_input(field_label, value=current_field_value)
        elif field_type == 'selectbox':
            # Now config can be asserted or checked to be SelectFieldConfig if needed for more specific keys
            options = config.get('options', []) # type: ignore
            format_function = config.get('format_func', lambda x: x) # type: ignore
            try:
                index = options.index(current_field_value) if current_field_value in options else 0
            except ValueError:
                index = 0
            form_data_submitted[field] = st.selectbox(field_label, options=options, index=index, format_func=format_function)
        elif field_type == 'date_input':
            val = current_field_value
            if pd.isna(val) or val is None:
                val = None
            elif isinstance(val, str):
                val = pd.to_datetime(val, errors='coerce').date()
            elif isinstance(val, datetime):
                val = val.date()
            val = val if isinstance(val, date) else None
            form_data_submitted[field] = st.date_input(field_label, value=val)
        elif field_type == 'time_input':
            val = current_field_value
            if pd.isna(val) or val is None:
                val = None
            elif isinstance(val, str):
                try:
                    val = datetime.strptime(val, '%H:%M:%S').time()
                except ValueError:
                    val = None
            if isinstance(val, time):
                form_data_submitted[field] = st.time_input(field_label, value=val)
            else:
                form_data_submitted[field] = st.time_input(field_label, value=None)
        elif field_type == 'text_area':
            form_data_submitted[field] = st.text_area(field_label, value=current_field_value)
        elif field_type == 'number_input':
            form_data_submitted[field] = st.number_input(
                field_label, value=current_field_value,
                min_value=config.get('min_value'), # type: ignore
                step=config.get('step', 1), # type: ignore
                format=config.get('format') # type: ignore
            )
    return form_data_submitted

def _save_entity_data(
    entity_type: str,
    repo: SQLModelRepository[Any],
    form_data_submitted: dict[str, Any],
    form_fields_config: FormConfig, # Updated type
    dialog_mode: str,
    editing_id: Any = None,
    parent_id_field_name: str | None = None,
    parent_id_value: Any | None = None
) -> bool:
    is_valid = all(
        not (config.get('required') and not form_data_submitted.get(field) and form_data_submitted.get(field) != 0) # type: ignore
        for field, config in form_fields_config.items()
    )
    if not is_valid:
        st.error("Por favor, preencha todos os campos obrigatórios (*).")
        return False

    current_time = datetime.now()
    save_data: dict[str, Any] = {k: v for k, v in form_data_submitted.items() if k in form_fields_config}

    if entity_type in ["item", "supplier", "competitor"] and "description" in save_data:
        save_data["desc"] = save_data.pop("description")

    if entity_type == "bidding":
        session_date_val = save_data.pop("session_date", None)
        session_time_val = save_data.pop("session_time", None)
        if session_date_val:
            save_data["date"] = datetime.combine(session_date_val, session_time_val if session_time_val else time.min)
        else:
            save_data["date"] = None

    for field, config_untyped in form_fields_config.items():
        config = config_untyped # Already FormFieldConfig, but for clarity if we need to check type
        if config['type'] == 'date_input' and isinstance(save_data.get(field), str):
            save_data[field] = pd.to_datetime(save_data[field], errors='coerce').date() if save_data.get(field) else None
        elif config['type'] == 'time_input' and isinstance(save_data.get(field), str):
            if save_data.get(field):
                try:
                    save_data[field] = datetime.strptime(save_data[field], '%H:%M:%S').time()
                except ValueError:
                    save_data[field] = None
            else:
                save_data[field] = None

    # title_singular is passed as a parameter to _manage_generic_dialog, which then passes it to _handle_entity_deletion.
    # _save_entity_data gets title_singular from _manage_generic_dialog's form_fields_config if it was put there,
    # or capitalizes entity_type. Since we removed setting it in _manage_generic_dialog, it will use capitalize.
    # For consistency and to avoid potential type issues if it *was* in the config as non-str:
    _title_singular_from_config = form_fields_config.get("_title_singular") # This key is not part of FormFieldConfig
    title_singular_display = str(_title_singular_from_config) if _title_singular_from_config else entity_type.capitalize()


    if entity_type in ["supplier", "competitor"]:
        fields_to_nullify_if_empty = ["website", "email", "phone", "desc"]
        for field_name in fields_to_nullify_if_empty:
            if field_name in save_data and save_data[field_name] == "":
                save_data[field_name] = None

    try:
        if dialog_mode == "new":
            save_data['created_at'] = current_time
            save_data['updated_at'] = current_time
            if parent_id_field_name and parent_id_value is not None:
                save_data[parent_id_field_name] = parent_id_value
            if 'id' in save_data:
                del save_data['id']

            new_entity_model = repo.model_class(**save_data)
            created_entity = repo.add(new_entity_model)
            display_name = getattr(created_entity, 'name', getattr(created_entity, 'process_number', ''))
            st.success(f"{title_singular_display} '{display_name}' (ID: {created_entity.id}) criado(a) com sucesso!")
            return True
        else:  # dialog_mode == "edit"
            if editing_id is None:
                st.error(f"ID de edição não fornecido para {title_singular_display}.")
                return False
            save_data['updated_at'] = current_time
            updated_entity = repo.update(editing_id, save_data)
            if updated_entity:
                display_name = getattr(updated_entity, 'name', getattr(updated_entity, 'process_number', ''))
                st.success(f"{title_singular_display} '{display_name}' (ID: {updated_entity.id}) atualizado(a) com sucesso!")
                return True
            else:
                st.error(f"Falha ao atualizar {str(title_singular_display).lower()} (ID: {editing_id}). Item não encontrado ou erro na atualização.")
                return False
    except Exception as e:
        st.error(f"Erro ao salvar {str(title_singular_display)}: {e}")
        return False

def _handle_entity_deletion(
    entity_type: str,
    repo: SQLModelRepository[Any],
    editing_id: Any,
    entity_data: dict[str, Any],
    related_entities_to_delete_config: dict[str, SQLModelRepository[Any]] | None,
    title_singular: str
) -> bool:
    item_repo_local = related_entities_to_delete_config.get('item_repo') if related_entities_to_delete_config else None
    quote_repo_local = related_entities_to_delete_config.get('quote_repo') if related_entities_to_delete_config else None
    bid_repo_local = related_entities_to_delete_config.get('bid_repo') if related_entities_to_delete_config else None

    entity_name_display = entity_data.get('name', entity_data.get('process_number', ''))

    related_entity_names = []
    if entity_type == 'bidding':
        related_entity_names = ["itens", "orçamentos dos itens", "lances dos itens"]
    elif entity_type == 'item':
        related_entity_names = ["orçamentos", "lances"]
    elif entity_type == 'supplier':
        related_entity_names = ["orçamentos"]
    elif entity_type == 'competitor':
        related_entity_names = ["lances"]

    warning_message = f"Tem certeza que deseja deletar {str(title_singular).lower()} '{entity_name_display}'?"
    if related_entity_names:
        warning_message += f" Todas as {', '.join(related_entity_names)} associadas também serão deletadas. Esta ação não pode ser desfeita."

    st.warning(warning_message)
    confirm_cols_del = st.columns(2)

    if confirm_cols_del[0].button("🔴 Confirmar Exclusão", type="primary", key=f"confirm_del_btn_{entity_type}", use_container_width=True):
        try:
            if entity_type == 'bidding':
                if item_repo_local and quote_repo_local and bid_repo_local:
                    all_items_from_repo = item_repo_local.get_all() or []
                    items_to_delete = [item for item in all_items_from_repo if item.bidding_id == editing_id]
                    for item_del in items_to_delete:
                        all_quotes_from_repo = quote_repo_local.get_all() or []
                        quotes_to_delete_for_item = [q for q in all_quotes_from_repo if q.item_id == item_del.id]
                        for quote_del in quotes_to_delete_for_item:
                            quote_repo_local.delete(quote_del.id)
                        all_bids_from_repo = bid_repo_local.get_all() or []
                        bids_to_delete_for_item = [b for b in all_bids_from_repo if b.item_id == item_del.id]
                        for bid_del in bids_to_delete_for_item:
                            bid_repo_local.delete(bid_del.id)
                        item_repo_local.delete(item_del.id)
            elif entity_type == 'item':
                if quote_repo_local and bid_repo_local:
                    all_quotes_from_repo = quote_repo_local.get_all() or []
                    quotes_to_delete = [q for q in all_quotes_from_repo if q.item_id == editing_id]
                    for quote_del in quotes_to_delete:
                        quote_repo_local.delete(quote_del.id)
                    all_bids_from_repo = bid_repo_local.get_all() or []
                    bids_to_delete = [b for b in all_bids_from_repo if b.item_id == editing_id]
                    for bid_del in bids_to_delete:
                        bid_repo_local.delete(bid_del.id)
            elif entity_type == 'supplier':
                if quote_repo_local:
                    all_quotes_from_repo = quote_repo_local.get_all() or []
                    quotes_to_delete = [q for q in all_quotes_from_repo if q.supplier_id == editing_id]
                    for quote_del in quotes_to_delete:
                        quote_repo_local.delete(quote_del.id)
            elif entity_type == 'competitor':
                if bid_repo_local:
                    all_bids_from_repo = bid_repo_local.get_all() or []
                    bids_to_delete = [b for b in all_bids_from_repo if b.competitor_id == editing_id]
                    for bid_del in bids_to_delete:
                        bid_repo_local.delete(bid_del.id)
            repo.delete(editing_id)
            st.success(f"{str(title_singular)} '{entity_name_display}' e suas dependências foram deletados(as) com sucesso.")
            if st.session_state.get(f'selected_{entity_type}_id') == editing_id:
                st.session_state[f'selected_{entity_type}_id'] = None
            if entity_type == 'bidding':
                st.session_state.selected_bidding_id = None
                st.session_state.selected_item_id = None
            if entity_type == 'item' and st.session_state.selected_item_id == editing_id:
                st.session_state.selected_item_id = None
            return True
        except Exception as e:
            st.error(f"Erro ao deletar {str(title_singular)} e/ou suas dependências: {e}")
            return False
    if confirm_cols_del[1].button("Cancelar", key=f"cancel_del_btn_{entity_type}", use_container_width=True):
        st.session_state[f'confirm_delete_{entity_type}'] = False
        st.rerun()
    return False

def _manage_generic_dialog(
    entity_type: str,
    repo: SQLModelRepository[Any],
    form_fields_config: FormConfig, # Updated Type
    title_singular: str,
    related_repos: dict[str, SQLModelRepository[Any]] | None = None,
    parent_id_field_name: str | None = None,
    parent_id_value: Any | None = None
):
    data: dict[str, Any] = {field: config.get('default') for field, config in form_fields_config.items()} # type: ignore
    dialog_mode = "new"
    editing_id_key = f'editing_{entity_type}_id'
    show_dialog_key = f'show_manage_{entity_type}_dialog'
    confirm_delete_key = f'confirm_delete_{entity_type}'

    if st.session_state[editing_id_key] is not None:
        try:
            entity_to_edit = repo.get(st.session_state[editing_id_key])
            if not entity_to_edit:
                st.error(f"{title_singular} não encontrado(a) para edição (ID: {st.session_state[editing_id_key]}).")
                st.session_state[show_dialog_key] = False
                st.session_state[editing_id_key] = None
                st.rerun()
                return
            for field_key, config_val_untyped in form_fields_config.items():
                config_val = config_val_untyped # Already FormFieldConfig
                model_attr = "desc" if field_key == "description" and entity_type in ["item", "supplier", "competitor"] else field_key
                if entity_type == "bidding" and field_key == "session_date":
                    data[field_key] = entity_to_edit.date.date() if hasattr(entity_to_edit, "date") and entity_to_edit.date else config_val.get('default')
                    continue
                elif entity_type == "bidding" and field_key == "session_time":
                    data[field_key] = entity_to_edit.date.time() if hasattr(entity_to_edit, "date") and entity_to_edit.date else config_val.get('default')
                    continue
                if hasattr(entity_to_edit, model_attr):
                    data[field_key] = getattr(entity_to_edit, model_attr)
                elif 'default' in config_val: # Check if default is actually in this specific config type
                    data[field_key] = config_val['default']
                else:
                    data[field_key] = '' # Or some other appropriate default
            data['id'] = entity_to_edit.id
            dialog_mode = "edit"
        except Exception as e:
            st.error(f"Erro ao carregar {title_singular} para edição: {e}")
            st.session_state[show_dialog_key] = False
            st.session_state[editing_id_key] = None
            st.rerun()
            return

    st.subheader(f"{'Editar' if dialog_mode == 'edit' else 'Novo(a)'} {title_singular}" + (f" (ID: {data.get('id')})" if dialog_mode == 'edit' else ""))

    with st.form(key=f"{entity_type}_form"):
        submitted_form_data = _render_form_fields(form_fields_config, data)
        form_action_cols = st.columns(2)
        with form_action_cols[0]:
            save_button_label = f"💾 Salvar {title_singular}" if dialog_mode == "new" else f"💾 Atualizar {title_singular}"
            if st.form_submit_button(save_button_label, use_container_width=True):
                if _save_entity_data(entity_type, repo, submitted_form_data, form_fields_config, dialog_mode, st.session_state[editing_id_key], parent_id_field_name, parent_id_value):
                    st.session_state[show_dialog_key] = False
                    st.session_state[editing_id_key] = None
                    st.rerun()
                else:
                    st.session_state[show_dialog_key] = True
                    st.rerun()

        if dialog_mode == "edit":
            with form_action_cols[1]:
                if st.form_submit_button(f"🗑️ Deletar {title_singular}", type="secondary", use_container_width=True):
                    st.session_state[confirm_delete_key] = True
                    st.rerun()

    if st.session_state.get(confirm_delete_key, False):
        if _handle_entity_deletion(entity_type, repo, st.session_state[editing_id_key], data, related_repos or {}, title_singular):
            st.session_state[show_dialog_key] = False
            st.session_state[editing_id_key] = None
            st.session_state[confirm_delete_key] = False
            st.rerun()
        else:
            if not st.session_state.get(f"cancel_del_btn_{entity_type}_clicked", False):
                 st.session_state[show_dialog_key] = True
            st.session_state.pop(f"cancel_del_btn_{entity_type}_clicked", None)
            st.rerun()

    if st.button("Fechar Diálogo", key=f"close_dialog_btn_{entity_type}", use_container_width=True):
        st.session_state[show_dialog_key] = False
        st.session_state[editing_id_key] = None
        st.session_state[confirm_delete_key] = False
        st.rerun()

# --- Funções Wrapper para Diálogos Específicos ---
bidding_repo: SQLModelRepository[Bidding] | None = None
item_repo: SQLModelRepository[Item] | None = None
supplier_repo: SQLModelRepository[Supplier] | None = None
competitor_repo: SQLModelRepository[Competitor] | None = None
quote_repo: SQLModelRepository[Quote] | None = None
bid_repo: SQLModelRepository[Bid] | None = None

def set_dialog_repositories(
    b_repo: SQLModelRepository[Bidding], i_repo: SQLModelRepository[Item],
    s_repo: SQLModelRepository[Supplier], c_repo: SQLModelRepository[Competitor],
    q_repo: SQLModelRepository[Quote], bi_repo: SQLModelRepository[Bid]
):
    global bidding_repo, item_repo, supplier_repo, competitor_repo, quote_repo, bid_repo
    bidding_repo = b_repo
    item_repo = i_repo
    supplier_repo = s_repo
    competitor_repo = c_repo
    quote_repo = q_repo
    bid_repo = bi_repo

@st.dialog("Gerenciar Licitação", width="large")
def manage_bidding_dialog_wrapper():
    if not bidding_repo or not item_repo or not quote_repo or not bid_repo:
        st.error("Repositórios não configurados para o diálogo de licitação.")
        return
    _manage_generic_dialog(
        'bidding', bidding_repo, bidding_form_config, "Licitação",
        related_repos={"item_repo": item_repo, "quote_repo": quote_repo, "bid_repo": bid_repo}
    )

@st.dialog("Gerenciar Item da Licitação", width="large")
def manage_item_dialog_wrapper():
    if not item_repo or not bidding_repo or not quote_repo or not bid_repo:
        st.error("Repositórios não configurados para o diálogo de item.")
        return

    parent_bidding_id = st.session_state.get('parent_bidding_id_for_item_dialog')
    if parent_bidding_id is None:
        st.error("Licitação pai não definida.")
        st.session_state.show_manage_item_dialog = False
        st.rerun()
        return

    parent_bidding = bidding_repo.get(parent_bidding_id)
    if not parent_bidding:
        st.error("Licitação pai não encontrada.")
        st.session_state.show_manage_item_dialog = False
        st.rerun()
        return
    st.info(f"Para Licitação: {parent_bidding.process_number} - {parent_bidding.city}")

    _manage_generic_dialog(
        'item', item_repo, item_form_config, "Item",
        related_repos={"quote_repo": quote_repo, "bid_repo": bid_repo},
        parent_id_field_name='bidding_id', parent_id_value=parent_bidding_id
    )

@st.dialog("Gerenciar Fornecedor", width="large")
def manage_supplier_dialog_wrapper():
    if not supplier_repo or not quote_repo:
        st.error("Repositórios não configurados para o diálogo de fornecedor.")
        return
    _manage_generic_dialog(
        'supplier', supplier_repo, contact_entity_form_config, "Fornecedor",
        related_repos={"quote_repo": quote_repo}
    )

@st.dialog("Gerenciar Concorrente", width="large")
def manage_competitor_dialog_wrapper():
    if not competitor_repo or not bid_repo:
        st.error("Repositórios não configurados para o diálogo de concorrente.")
        return
    _manage_generic_dialog(
        'competitor', competitor_repo, contact_entity_form_config, "Concorrente",
        related_repos={"bid_repo": bid_repo}
    )
# Example of how repositories might be set from app.py after they are initialized:
# from ui import dialogs
# dialogs.set_dialog_repositories(bidding_repo, item_repo, supplier_repo, competitor_repo, quote_repo, bid_repo)
# This setup call would need to happen once before any dialog is invoked.
# This also implies that the ui.dialogs module is imported in app.py.
# The actual repo instances (bidding_repo, etc.) would come from db.database.py or similar.
# This will be handled in the app.py refactoring step.
# For now, this file can be created, but the dialogs won't be fully functional.
# The crucial part is that the function signatures and internal logic are moved.
# The dependency injection for repositories will be finalized in the next step.
