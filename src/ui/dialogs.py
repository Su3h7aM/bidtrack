import streamlit as st
import pandas as pd
from datetime import datetime, time, date
from typing import Any, cast

# Models
from db.models import Bidding, Item, Supplier, Bidder, Quote, Bid, BiddingMode # Competitor -> Bidder

# Repository type hint (still needed for parameters and module-level vars)
from repository.sqlmodel import SQLModelRepository # Updated import for new location


# --- Module-level repository instances, to be set by set_dialog_repositories ---
# These will be accessed by the dialog wrapper functions.
_bidding_repo: SQLModelRepository[Bidding] | None = None
_item_repo: SQLModelRepository[Item] | None = None
_supplier_repo: SQLModelRepository[Supplier] | None = None
_bidder_repo: SQLModelRepository[Bidder] | None = None # _competitor_repo -> _bidder_repo
_quote_repo: SQLModelRepository[Quote] | None = None
_bid_repo: SQLModelRepository[Bid] | None = None


# --- Definições de Configuração dos Formulários ---
bidding_form_config = {
    "process_number": {
        "label": "Nº do Processo*",
        "type": "text_input",
        "required": True,
    },
    "city": {"label": "Cidade*", "type": "text_input", "required": True},
    "mode": {
        "label": "Modalidade*",
        "type": "selectbox",
        "options": list(BiddingMode),
        "required": True,
        "default": BiddingMode.PE,  # Default to BiddingMode.PE enum member
        "format_func": lambda mode: mode.value,  # Format function to display enum value
    },
    "session_date": {
        "label": "Data da Sessão (Opcional)",
        "type": "date_input",
        "default": None,
    },
    "session_time": {
        "label": "Hora da Sessão (Opcional)",
        "type": "time_input",
        "default": None,
    },
}
item_form_config = {
    "name": {"label": "Nome do Item*", "type": "text_input", "required": True},
    "description": {"label": "Descrição", "type": "text_area", "default": ""},
    "code": {"label": "Código", "type": "text_input", "required": False, "default": ""},
    "quantity": {
        "label": "Quantidade*",
        "type": "number_input",
        "min_value": 1.0,
        "default": 1.0,
        "required": True,
        "step": 1.0,
    },
    "unit": {
        "label": "Unidade*",
        "type": "text_input",
        "default": "UN",
        "required": True,
    },
    "notes": {
        "label": "Observações",
        "type": "text_area",
        "default": "",
        "required": False,
    },
}
contact_entity_form_config = {
    "name": {"label": "Nome*", "type": "text_input", "required": True},
    "website": {"label": "Website", "type": "text_input", "default": ""},
    "email": {"label": "Email", "type": "text_input", "default": ""},
    "phone": {"label": "Telefone", "type": "text_input", "default": ""},
    "description": {
        "label": "Descrição/Observações",
        "type": "text_area",
        "default": "",
    },
}

# --- Helper Functions for _manage_generic_dialog ---


def _render_form_fields(
    form_fields_config: dict[str, dict[str, Any]], current_data: dict[str, Any]
) -> dict[str, Any]:
    """Renders form fields based on configuration and current data."""
    form_data_submitted = {}
    for field, config in form_fields_config.items():
        if not isinstance(config, dict):
            continue
        field_label = config.get("label", field.replace("_", " ").title())
        current_field_value = current_data.get(field, config.get("default", ""))

        if config["type"] == "text_input":
            form_data_submitted[field] = st.text_input(
                field_label, value=current_field_value
            )
        elif config["type"] == "selectbox":
            options = config.get("options", [])
            format_function = config.get(
                "format_func", lambda x: x
            )  # Get format_func from config
            try:
                # current_field_value should be an enum member if editing, or the default enum member
                index = (
                    options.index(current_field_value)
                    if current_field_value in options
                    else 0
                )
            except ValueError:
                index = 0
            form_data_submitted[field] = st.selectbox(
                field_label, options=options, index=index, format_func=format_function
            )
        elif config["type"] == "date_input":
            val = current_field_value
            if pd.isna(val) or val is None:
                val = None
            elif isinstance(val, str):
                val = pd.to_datetime(val, errors="coerce").date()
            elif isinstance(val, datetime):
                val = val.date()
            # Ensure val is a date object or None for st.date_input
            val = val if isinstance(val, date) else None
            form_data_submitted[field] = st.date_input(field_label, value=val)
        elif config["type"] == "time_input":
            val = current_field_value
            if pd.isna(val) or val is None:
                val = None
            elif isinstance(val, str):
                try:
                    val = datetime.strptime(val, "%H:%M:%S").time()
                except ValueError:
                    val = None
            # Ensure val is a time object or None for st.time_input
            val = val if isinstance(val, time) else None
            form_data_submitted[field] = st.time_input(field_label, value=val)
        elif config["type"] == "text_area":
            form_data_submitted[field] = st.text_area(
                field_label, value=current_field_value
            )
        elif config["type"] == "number_input":
            form_data_submitted[field] = st.number_input(
                field_label,
                value=current_field_value,
                min_value=config.get("min_value"),
                step=config.get("step", 1),
                format=config.get("format"),
            )
    return form_data_submitted


def _save_entity_data(
    entity_type: str,
    repo: SQLModelRepository,
    form_data_submitted: dict[str, Any],
    form_fields_config: dict[str, dict[str, Any]],
    dialog_mode: str,
    editing_id: Any = None,
    parent_id_field_name: str = None,
    parent_id_value: Any = None,
) -> bool:
    """Saves entity data (create or update) by calling core services. Returns True on success."""
    # Ensure the correct repository is available (it's passed as 'repo' argument)
    if repo is None:
        st.error("Repositório não configurado para esta operação.")
        return False

    is_valid = all(
        not (
            config.get("required")
            and not form_data_submitted.get(field)
            and form_data_submitted.get(field) != 0 # Check for 0 as a valid input
        )
        for field, config in form_fields_config.items()
        if isinstance(config, dict)
    )
    if not is_valid:
        st.error("Por favor, preencha todos os campos obrigatórios (*).")
        return False

    # Prepare data, excluding fields not in form_fields_config
    # and handling specific mappings like description -> desc
    data_to_save = {
        k: v for k, v in form_data_submitted.items() if k in form_fields_config
    }
    if entity_type in ["item", "supplier", "bidder"] and "description" in data_to_save: # competitor -> bidder
        data_to_save["desc"] = data_to_save.pop("description")

    # Handle Bidding specific date/time combination
    if entity_type == "bidding":
        session_date_val = data_to_save.pop("session_date", None)
        session_time_val = data_to_save.pop("session_time", None)
        if session_date_val:
            data_to_save["date"] = datetime.combine(
                session_date_val, session_time_val if session_time_val else time.min
            )
        else:
            data_to_save["date"] = None

    # Generic conversion of empty strings to None for optional text fields
    for field_name_from_config, field_config in form_fields_config.items():
        if isinstance(field_config, dict):  # Ensure it's a field configuration
            is_required = field_config.get("required", False)
            field_type = field_config.get("type", "")

            if not is_required and field_type in ["text_input", "text_area"]:
                # Determine the actual key in data_to_save (could have been aliased)
                actual_key_in_data = field_name_from_config
                if entity_type in ["item", "supplier", "bidder"] and field_name_from_config == "description": # competitor -> bidder
                    actual_key_in_data = "desc"

                if actual_key_in_data in data_to_save and data_to_save[actual_key_in_data] == "":
                    data_to_save[actual_key_in_data] = None

    title_singular = form_fields_config.get("_title_singular", entity_type.capitalize())

    try:
        if dialog_mode == "new":
            if parent_id_field_name and parent_id_value is not None:
                data_to_save[parent_id_field_name] = parent_id_value

            # Directly use repo.model (which should be the SQLModel class)
            # The type of repo is SQLModelRepository[T], so repo.model is type[T]
            model_cls = repo.model
            model_instance = model_cls(**data_to_save)
            created_entity = repo.add(model_instance)

            display_name = getattr(created_entity, "name", getattr(created_entity, "process_number", str(created_entity.id)))
            st.success(f"{title_singular} '{display_name}' (ID: {created_entity.id}) criado(a) com sucesso!")

        else:  # dialog_mode == "edit"
            if editing_id is None:
                st.error(f"ID de edição não fornecido para {title_singular}.")
                return False

            # For updates, data_to_save is the dict of fields to update
            # No need to fetch the entity first if repo.update handles partial updates with a dict
            # The repository's update method takes (item_id: int, item_data: dict[str, Any])
            # Ensure 'id', 'created_at', 'updated_at' are not in data_to_save for update
            update_dict = {k: v for k, v in data_to_save.items() if k not in ['id', 'created_at', 'updated_at']}

            updated_entity = repo.update(editing_id, update_dict)

            if updated_entity is None:
                st.error(f"Falha ao atualizar {title_singular} com ID {editing_id}. Entidade não encontrada.")
                return False

            display_name = getattr(updated_entity, "name", getattr(updated_entity, "process_number", str(updated_entity.id)))
            st.success(f"{title_singular} '{display_name}' (ID: {updated_entity.id}) atualizado(a) com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar {title_singular}: {e}")
        return False


def _handle_entity_deletion(
    entity_type: str,
    repo: SQLModelRepository, # Primary repository for the entity being deleted
    editing_id: Any,
    entity_name_display: str,
    title_singular: str,
) -> bool:
    """Handles entity deletion using direct repository call, relying on DB/ORM cascades."""

    warning_message = (
        f"Tem certeza que deseja deletar {title_singular.lower()} '{entity_name_display}'? "
        "Todas as informações relacionadas (itens, orçamentos, lances) serão automaticamente "
        "deletadas devido às regras de cascata estabelecidas no banco de dados."
    )
    st.warning(warning_message)

    confirm_cols_del = st.columns(2)

    if confirm_cols_del[0].button("🔴 Confirmar Exclusão", type="primary", key=f"confirm_del_btn_{entity_type}", use_container_width=True):
        try:
            if repo.delete(editing_id): # Assuming repo.delete returns True on success
                st.success(
                    f"{title_singular} '{entity_name_display}' e suas dependências foram deletados(as) com sucesso."
                )
                # Update session state for selections
                if st.session_state.get(f"selected_{entity_type}_id") == editing_id:
                    st.session_state[f"selected_{entity_type}_id"] = None
                if entity_type == "bidding": # Special handling for bidding selection cascade
                    st.session_state.selected_bidding_id = None
                    st.session_state.selected_item_id = None
                if entity_type == "item" and st.session_state.get("selected_item_id") == editing_id:
                     st.session_state.selected_item_id = None
                return True # Deletion successful
            else:
                st.error(f"Falha ao deletar {title_singular} '{entity_name_display}'. O item pode não existir mais ou a exclusão falhou no repositório.")
                return False
        except Exception as e:
            st.error(f"Erro ao deletar {title_singular}: {e}")
            return False # Deletion failed

    if confirm_cols_del[1].button("Cancelar", key=f"cancel_del_btn_{entity_type}", use_container_width=True):
        st.session_state[f"confirm_delete_{entity_type}"] = False
        st.rerun()
    return False


# --- Refactored Generic Dialog Management ---
def _manage_generic_dialog(
    entity_type: str,
    repo: SQLModelRepository, # This is the primary repository for the entity type being managed
    form_fields_config: dict[str, Any],
    title_singular: str,
    # related_repos are no longer passed here, _handle_entity_deletion will use module-level ones
    parent_id_field_name: str | None = None,
    parent_id_value: Any = None,
):
    data: dict[str, Any] = {
        field: config.get("default", "")
        for field, config in form_fields_config.items()
        if isinstance(config, dict)
    }
    dialog_mode = "new"
    editing_id_key = f"editing_{entity_type}_id"
    show_dialog_key = f"show_manage_{entity_type}_dialog"
    confirm_delete_key = f"confirm_delete_{entity_type}"

    form_fields_config["_title_singular"] = title_singular

    editing_id = st.session_state.get(editing_id_key)

    if editing_id is not None:
        dialog_mode = "edit"
        entity_to_edit: Any = None # Should be T | None
        try:
            # Fetch entity using direct repository call
            # repo is already the specific repository instance, e.g., _bidding_repo
            entity_to_edit = repo.get(editing_id)

            if not entity_to_edit:
                st.error(f"{title_singular} não encontrado(a) para edição (ID: {editing_id}).")
                st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun(); return

            # Populate 'data' dict from the fetched entity for the form
            for field_key, config_val in form_fields_config.items():
                if isinstance(config_val, dict): # Ensure it's a field config
                    model_attr = "desc" if field_key == "description" and entity_type in ["item", "supplier", "bidder"] else field_key # competitor -> bidder

                    if entity_type == "bidding" and field_key == "session_date":
                        data[field_key] = entity_to_edit.date.date() if hasattr(entity_to_edit, "date") and entity_to_edit.date else config_val.get("default")
                    elif entity_type == "bidding" and field_key == "session_time":
                        data[field_key] = entity_to_edit.date.time() if hasattr(entity_to_edit, "date") and entity_to_edit.date else config_val.get("default")
                    elif hasattr(entity_to_edit, model_attr):
                        data[field_key] = getattr(entity_to_edit, model_attr)
                    elif "default" in config_val: # Fallback to default if attribute missing (should not happen with SQLModel)
                        data[field_key] = config_val["default"]
                    else:
                        data[field_key] = "" # Or None, depending on desired behavior for missing attrs
            data["id"] = entity_to_edit.id # Ensure ID is part of data for display

        except Exception as e:
            st.error(f"Erro ao carregar {title_singular} para edição: {e}")
            st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun(); return

    st.subheader(f"{'Editar' if dialog_mode == 'edit' else 'Novo(a)'} {title_singular}" + (f" (ID: {data.get('id')})" if dialog_mode == "edit" else ""))

    with st.form(key=f"{entity_type}_form"):
        submitted_form_data = _render_form_fields(form_fields_config, data)
        form_action_cols = st.columns(2)
        with form_action_cols[0]:
            save_button_label = f"💾 Salvar {title_singular}" if dialog_mode == "new" else f"💾 Atualizar {title_singular}"
            if st.form_submit_button(save_button_label, use_container_width=True):
                if _save_entity_data(entity_type, repo, submitted_form_data, form_fields_config, dialog_mode, editing_id, parent_id_field_name, parent_id_value):
                    st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.rerun()
                else: # Save failed, keep dialog open
                    st.session_state[show_dialog_key] = True # Ensure dialog stays open
                    # No rerun here, let error messages display within the current form render

        if dialog_mode == "edit":
            with form_action_cols[1]:
                if st.form_submit_button(f"🗑️ Deletar {title_singular}", type="secondary", use_container_width=True):
                    st.session_state[confirm_delete_key] = True
                    # NO st.rerun() here.

    if st.session_state.get(confirm_delete_key, False):
        entity_name_display = data.get("name", data.get("process_number", str(editing_id)))
        if _handle_entity_deletion(entity_type, repo, editing_id, entity_name_display, title_singular):
            st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.session_state[confirm_delete_key] = False; st.rerun()
        else: # Deletion failed or cancelled
            if st.session_state.get(confirm_delete_key):
                 st.session_state[show_dialog_key] = True

    if st.button("Fechar Diálogo", key=f"close_dialog_btn_{entity_type}", use_container_width=True):
        st.session_state[show_dialog_key] = False; st.session_state[editing_id_key] = None; st.session_state[confirm_delete_key] = False; st.rerun()


# --- Funções Wrapper para Diálogos Específicos ---
# These wrappers will now use the module-level underscore-prefixed repository instances.

# The user of these functions will need to set these repository variables,
# perhaps through a setup function or by importing them from where they are initialized.
def set_dialog_repositories(
    b_repo: SQLModelRepository[Bidding],
    i_repo: SQLModelRepository[Item],
    s_repo: SQLModelRepository[Supplier],
    bd_repo: SQLModelRepository[Bidder], # c_repo -> bd_repo, Competitor -> Bidder
    q_repo: SQLModelRepository[Quote],
    bi_repo: SQLModelRepository[Bid],
):
    global _bidding_repo, _item_repo, _supplier_repo, _bidder_repo, _quote_repo, _bid_repo # _competitor_repo -> _bidder_repo
    _bidding_repo = b_repo
    _item_repo = i_repo
    _supplier_repo = s_repo
    _bidder_repo = bd_repo # _competitor_repo -> _bidder_repo, c_repo -> bd_repo
    _quote_repo = q_repo
    _bid_repo = bi_repo


@st.dialog("Gerenciar Licitação", width="large")
def manage_bidding_dialog_wrapper():
    if not _bidding_repo or not _item_repo or not _quote_repo or not _bid_repo:
        st.error("Repositórios não configurados para o diálogo de licitação.")
        if st.button("Fechar"): st.rerun()
        return
    _manage_generic_dialog(
        "bidding",
        _bidding_repo, # Pass the main repo for this entity type
        bidding_form_config,
        "Licitação",
        # related_repos argument removed, _handle_entity_deletion uses module repos
    )


@st.dialog("Gerenciar Item da Licitação", width="large")
def manage_item_dialog_wrapper():
    if not _item_repo or not _bidding_repo or not _quote_repo or not _bid_repo:
        st.error("Repositórios não configurados para o diálogo de item.")
        if st.button("Fechar"): st.rerun()
        return

    parent_bidding_id = st.session_state.get("parent_bidding_id_for_item_dialog")
    if parent_bidding_id is None:
        st.error("Licitação pai não definida."); st.session_state.show_manage_item_dialog = False; st.rerun(); return

    # Fetch parent bidding using direct repository call to display info
    if _bidding_repo: # Check if _bidding_repo is initialized
        parent_bidding = _bidding_repo.get(parent_bidding_id)
        if not parent_bidding:
            st.error("Licitação pai não encontrada."); st.session_state.show_manage_item_dialog = False; st.rerun(); return
        st.info(f"Para Licitação: {parent_bidding.process_number} - {parent_bidding.city}")
    else:
        st.error("Repositório de Licitações não configurado."); st.session_state.show_manage_item_dialog = False; st.rerun(); return

    _manage_generic_dialog(
        "item",
        _item_repo, # Pass the main repo for this entity type
        item_form_config,
        "Item",
        # related_repos argument removed
        parent_id_field_name="bidding_id",
        parent_id_value=parent_bidding_id,
    )


@st.dialog("Gerenciar Fornecedor", width="large")
def manage_supplier_dialog_wrapper():
    if not _supplier_repo or not _quote_repo:
        st.error("Repositórios não configurados para o diálogo de fornecedor.")
        if st.button("Fechar"): st.rerun()
        return
    _manage_generic_dialog(
        "supplier",
        _supplier_repo, # Pass the main repo for this entity type
        contact_entity_form_config,
        "Fornecedor",
        # related_repos argument removed
    )


@st.dialog("Gerenciar Licitante", width="large") # "Concorrente" -> "Licitante"
def manage_bidder_dialog_wrapper(): # Renamed function
    if not _bidder_repo or not _bid_repo: # _competitor_repo -> _bidder_repo
        st.error("Repositórios não configurados para o diálogo de licitante.") # "concorrente" -> "licitante"
        if st.button("Fechar"): st.rerun()
        return
    _manage_generic_dialog(
        "bidder", # "competitor" -> "bidder"
        _bidder_repo, # _competitor_repo -> _bidder_repo
        contact_entity_form_config,
        "Licitante", # "Concorrente" -> "Licitante"
        # related_repos argument removed
    )


# Example of how repositories might be set from app.py after they are initialized:
# from ui import dialogs
# dialogs.set_dialog_repositories(bidding_repo, item_repo, supplier_repo, bidder_repo, quote_repo, bid_repo) # competitor_repo -> bidder_repo
# This setup call would need to happen once before any dialog is invoked.
# This also implies that the ui.dialogs module is imported in app.py.
# The actual repo instances (bidding_repo, etc.) would come from db.database.py or similar.
# This will be handled in the app.py refactoring step.
# For now, this file can be created, but the dialogs won't be fully functional.
# The crucial part is that the function signatures and internal logic are moved.
# The dependency injection for repositories will be finalized in the next step.
