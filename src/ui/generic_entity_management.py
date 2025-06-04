import streamlit as st
import pandas as pd
from decimal import Decimal
from ui.utils import get_options_map

# Helper function to load and prepare data for tabs (can be used as a default)
def load_and_prepare_data(repository, entity_name: str, columns_to_display: list[str] = None, selected_foreign_keys: dict = None):
    """
    Loads data from the given repository, prepares it, and handles errors.
    Can also filter by selected foreign keys if provided.
    """
    try:
        data_list = repository.get_all()
    except Exception as e:
        st.error(f"Erro ao carregar dados de {entity_name}: {e}")
        return pd.DataFrame()

    if not data_list:
        st.info(f"Nenhum(a) {entity_name.lower()} cadastrado(a).")
        return pd.DataFrame()

    try:
        df = pd.DataFrame([item.model_dump() for item in data_list])
    except Exception as e:
        st.error(f"Erro ao converter dados de {entity_name} para DataFrame: {e}")
        return pd.DataFrame()

    if df.empty:
        return df

    if selected_foreign_keys:
        for fk_column, fk_id in selected_foreign_keys.items():
            if fk_id is not None and fk_column in df.columns:
                df = df[df[fk_column] == fk_id]
            elif fk_id is None and fk_column in df.columns:
                return pd.DataFrame()
        if df.empty:
            st.info(f"Nenhum(a) {entity_name.lower()} encontrado(a) para a seleção atual.")

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce').dt.tz_localize(None)
    if "updated_at" in df.columns:
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors='coerce').dt.tz_localize(None)

    if columns_to_display:
        final_cols = []
        for col in columns_to_display:
            if col not in df.columns:
                df[col] = None
            final_cols.append(col)
        if 'id' not in final_cols and 'id' in df.columns:
            final_cols.append('id')
        elif 'id' not in df.columns:
            st.error(f"DataFrame para {entity_name} não possui coluna 'id', edições não serão possíveis.")
            return df[final_cols].copy() if final_cols else pd.DataFrame()
        return df[final_cols].copy()

    return df.copy()

def display_search_box_and_filter_df(df_unfiltered: pd.DataFrame, search_columns: list[str], search_key_suffix: str, entity_name_plural: str, search_label: str = None):
    if df_unfiltered is None or df_unfiltered.empty:
        return df_unfiltered
    if search_label is None:
        search_label = f"Buscar em {entity_name_plural} (por {', '.join(search_columns)}):"
    search_term = st.text_input(search_label, key=f"search_{search_key_suffix}")
    if not search_term:
        return df_unfiltered
    search_term_lower = search_term.lower()
    valid_search_columns = [col for col in search_columns if col in df_unfiltered.columns]
    if not valid_search_columns:
        return df_unfiltered
    combined_filter = pd.Series([False] * len(df_unfiltered), index=df_unfiltered.index)
    for col in valid_search_columns:
        try:
            combined_filter |= df_unfiltered[col].astype(str).str.lower().str.contains(search_term_lower, na=False)
        except Exception:
            pass
    df_filtered = df_unfiltered[combined_filter]
    if df_filtered.empty and search_term:
        st.info(f"Nenhum resultado encontrado para sua busca em {entity_name_plural}.")
    return df_filtered

# Updated to accept is_editable
def display_data_editor(df_to_edit: pd.DataFrame, column_config: dict, editor_key_suffix: str, is_editable: bool = True):
    if df_to_edit is None or df_to_edit.empty:
        return df_to_edit
    if 'id' not in df_to_edit.columns and not df_to_edit.empty:
         st.warning("A coluna 'id' é necessária para a edição mas não está presente no DataFrame fornecido ao editor.")
         return df_to_edit

    edited_df = st.data_editor(
        df_to_edit,
        key=f"editor_{editor_key_suffix}",
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        disabled=not is_editable # Set disabled state
    )
    return edited_df

def handle_save_changes(
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame,
    repository,
    entity_name_singular: str,
    editable_columns: list[str],
    required_fields: list[str] = None,
    decimal_fields: list[str] = None,
    special_conversions: dict = None,
    fields_to_remove_before_update: list[str] = None
):
    if required_fields is None: required_fields = []
    if decimal_fields is None: decimal_fields = []
    if special_conversions is None: special_conversions = {}
    default_non_updatable = ['id', 'created_at', 'updated_at']
    if fields_to_remove_before_update is None:
        fields_to_remove = default_non_updatable
    else:
        fields_to_remove = list(set(default_non_updatable + fields_to_remove_before_update))
    changes_processed_any_row = False
    if original_df is None or edited_df is None :
        return False
    if original_df.empty and edited_df.empty:
        st.info(f"Nenhum dado para salvar em {entity_name_singular.lower()}s.")
        return False
    if not original_df.empty and 'id' not in original_df.columns:
        st.error(f"Coluna 'id' não encontrada no DataFrame original de {entity_name_singular}. Não é possível salvar alterações.")
        return False
    if not edited_df.empty and 'id' not in edited_df.columns:
        st.error(f"Coluna 'id' não encontrada no DataFrame editado de {entity_name_singular}. Não é possível salvar alterações.")
        return False
    original_df_cleaned = original_df.dropna(subset=['id']) if 'id' in original_df.columns else original_df
    edited_df_cleaned = edited_df.dropna(subset=['id']) if 'id' in edited_df.columns else edited_df
    if not edited_df_cleaned.empty and original_df_cleaned.empty and not edited_df_cleaned.set_index('id').index.difference(original_df_cleaned.set_index('id').index).empty :
        st.info(f"Novas linhas foram adicionadas. Esta função salva apenas alterações em linhas existentes. Use a funcionalidade de criação para novos {entity_name_singular.lower()}s.")
    original_df_indexed = original_df_cleaned.set_index('id', drop=False) if not original_df_cleaned.empty else pd.DataFrame(columns=original_df.columns).set_index('id', drop=False)
    edited_df_indexed = edited_df_cleaned.set_index('id', drop=False) if not edited_df_cleaned.empty else pd.DataFrame(columns=edited_df.columns).set_index('id', drop=False)
    for entity_id, edited_row_series in edited_df_indexed.iterrows():
        if entity_id not in original_df_indexed.index:
            continue
        original_row_series = original_df_indexed.loc[entity_id]
        current_row_update_dict = {}
        row_had_actual_changes = False
        skip_this_row_due_to_error = False
        temp_changed_values_dict = {}
        for col_name_from_editor in editable_columns:
            if col_name_from_editor not in edited_row_series.index or col_name_from_editor not in original_row_series.index:
                continue
            original_value = original_row_series[col_name_from_editor]
            edited_value = edited_row_series[col_name_from_editor]
            changed = False
            if pd.isna(original_value) and pd.isna(edited_value): changed = False
            elif pd.isna(original_value) or pd.isna(edited_value): changed = True
            elif isinstance(original_value, pd.Timestamp) and isinstance(edited_value, pd.Timestamp):
                ts_original = original_value.tz_localize(None) if original_value.tzinfo else original_value
                ts_edited = edited_value.tz_localize(None) if edited_value.tzinfo else edited_value
                changed = ts_original != ts_edited
            elif isinstance(original_value, pd.Timestamp) or isinstance(edited_value, pd.Timestamp): changed = True
            elif isinstance(original_value, Decimal):
                try:
                    str_edited_value = str(edited_value).strip()
                    if not str_edited_value and original_value is not None : changed = True
                    elif not str_edited_value and original_value is None: changed = False
                    else: changed = original_value != Decimal(str_edited_value)
                except: changed = True
            elif isinstance(edited_value, Decimal) and not isinstance(original_value, Decimal):
                 try:
                    str_original_value = str(original_value).strip()
                    if not str_original_value and edited_value is not None: changed = True
                    elif not str_original_value and edited_value is None: changed = False
                    else: changed = Decimal(str_original_value) != edited_value
                 except: changed = True
            else:
                if type(original_value) != type(edited_value) and not (pd.isna(original_value) and pd.isna(edited_value)):
                    try:
                        casted_edited_value = type(original_value)(edited_value)
                        changed = original_value != casted_edited_value
                    except (ValueError, TypeError): changed = True
                else: changed = original_value != edited_value
            if changed:
                temp_changed_values_dict[col_name_from_editor] = edited_value
                row_had_actual_changes = True
        if not row_had_actual_changes: continue
        changes_processed_any_row = True
        for col_name_from_editor, raw_edited_value in temp_changed_values_dict.items():
            target_field = col_name_from_editor
            try:
                if col_name_from_editor in special_conversions:
                    conv_details = special_conversions[col_name_from_editor]
                    target_field = conv_details["target_field"]
                    conversion_func = conv_details["conversion_func"]
                    current_row_update_dict[target_field] = conversion_func(raw_edited_value)
                else:
                    current_row_update_dict[target_field] = raw_edited_value
            except Exception as e:
                st.error(f"{entity_name_singular} ID {entity_id}: Erro ao converter '{col_name_from_editor}' ('{raw_edited_value}') para '{target_field}': {e}.")
                skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue
        for req_field_target_name in required_fields:
            value_to_check = current_row_update_dict.get(req_field_target_name)
            if req_field_target_name in current_row_update_dict:
                if value_to_check is None or (isinstance(value_to_check, str) and not value_to_check.strip()):
                    editor_col_for_error = req_field_target_name
                    for cn_editor, conv_details in special_conversions.items():
                        if conv_details.get("target_field") == req_field_target_name:
                            editor_col_for_error = cn_editor; break
                    st.error(f"{entity_name_singular} ID {entity_id}: Campo obrigatório '{editor_col_for_error}' (destino: '{req_field_target_name}') está vazio. Alterações não salvas.")
                    skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue
        for dec_field_target_name in decimal_fields:
            if dec_field_target_name in current_row_update_dict:
                val = current_row_update_dict[dec_field_target_name]
                if val is not None and not isinstance(val, Decimal):
                    try:
                        str_val = str(val).strip()
                        if not str_val: current_row_update_dict[dec_field_target_name] = None
                        else: current_row_update_dict[dec_field_target_name] = Decimal(str_val)
                    except Exception as e:
                        editor_col_for_error = dec_field_target_name
                        for cn_editor, conv_details in special_conversions.items():
                           if conv_details.get("target_field") == dec_field_target_name: editor_col_for_error = cn_editor; break
                        st.error(f"{entity_name_singular} ID {entity_id}: Valor inválido para campo decimal '{editor_col_for_error}' ('{val}'): {e}.")
                        skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue
        for field_to_rm in fields_to_remove:
            current_row_update_dict.pop(field_to_rm, None)
        if not current_row_update_dict: continue
        try:
            repository.update(entity_id, current_row_update_dict)
            st.success(f"{entity_name_singular} ID {entity_id} atualizado(a) com sucesso.")
        except Exception as e:
            st.error(f"Falha ao salvar {entity_name_singular} ID {entity_id}: {e}. Tentativa de payload: {current_row_update_dict}")
    if not changes_processed_any_row:
        is_identical = False
        if not original_df_indexed.empty and not edited_df_indexed.empty:
            common_indices = original_df_indexed.index.intersection(edited_df_indexed.index)
            if not common_indices.empty:
                common_columns = original_df_indexed.columns.intersection(edited_df_indexed.columns)
                is_identical = original_df_indexed.loc[common_indices, common_columns].equals(edited_df_indexed.loc[common_indices, common_columns])
        elif original_df_indexed.empty and edited_df_indexed.empty:
            is_identical = True
        if is_identical:
            st.info(f"Nenhuma alteração detectada para salvar em {entity_name_singular.lower()}s.")
    return changes_processed_any_row

def display_entity_management_ui(
    repository,
    entity_name_singular: str,
    entity_name_plural: str,
    columns_to_display: list[str],
    column_config: dict,
    search_columns: list[str],
    editable_columns: list[str],
    required_fields: list[str] = None,
    decimal_fields: list[str] = None,
    special_conversions: dict = None,
    fields_to_remove_before_update: list[str] = None,
    custom_search_label: str = None,
    editor_key_suffix: str = None,
    foreign_key_selection_configs: list[dict] = None,
    custom_dataframe_preparation_func: callable = None,
    custom_data_processing_hook: callable = None,
    is_editable: bool = True,
    auto_save: bool = False # New parameter for auto-save
):
    if required_fields is None: required_fields = []
    if decimal_fields is None: decimal_fields = []
    if special_conversions is None: special_conversions = {}
    if foreign_key_selection_configs is None: foreign_key_selection_configs = []

    key_suffix = editor_key_suffix if editor_key_suffix else entity_name_singular.lower().replace(" ", "_")
    st.subheader(f"Gerenciar {entity_name_plural}")

    selected_foreign_key_ids = {}
    proceed_to_data_display = True

    for fk_config in foreign_key_selection_configs:
        fk_label = fk_config.get("label", "Selecione")
        fk_repo = fk_config.get("repository_for_options")
        fk_options_map_config = fk_config.get("options_map_config", {})
        fk_key = f"select_{fk_config.get('filter_column_on_df', fk_repo.__class__.__name__)}_{key_suffix}"
        options_data_list = None
        try:
            options_data_list = fk_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar opções para {fk_label}: {e}")
            proceed_to_data_display = False; break
        options_map, option_ids = get_options_map(
            data_list=options_data_list if options_data_list else [],
            name_col=fk_options_map_config.get("name_col", "name"),
            extra_cols=fk_options_map_config.get("extra_cols"),
            default_message=fk_options_map_config.get("default_message", "Selecione...")
        )
        selected_id = st.selectbox(fk_label, options=option_ids, format_func=lambda x: options_map.get(x, "Selecione..."), key=fk_key)
        filter_col_name = fk_config.get("filter_column_on_df")
        if filter_col_name:
            selected_foreign_key_ids[filter_col_name] = selected_id
        if selected_id is None and fk_config.get("block_if_parent_not_selected", True):
            st.info(f"Por favor, {fk_label.lower()} para continuar.")
            proceed_to_data_display = False
    df_display_unfiltered = pd.DataFrame()
    if proceed_to_data_display:
        if custom_dataframe_preparation_func:
            try:
                df_display_unfiltered = custom_dataframe_preparation_func(repository, selected_foreign_key_ids)
                if df_display_unfiltered is None:
                    st.error(f"Falha ao preparar dados customizados para {entity_name_plural}.")
                    df_display_unfiltered = pd.DataFrame()
            except Exception as e:
                st.error(f"Erro na função de preparação de dados customizada para {entity_name_plural}: {e}")
                df_display_unfiltered = pd.DataFrame()
        else:
            df_raw = load_and_prepare_data(repository, entity_name_plural, selected_foreign_keys=selected_foreign_key_ids)
            if df_raw is not None:
                 df_display_unfiltered = df_raw
            else:
                 df_display_unfiltered = pd.DataFrame() if df_raw is None else df_raw
        if custom_data_processing_hook and df_display_unfiltered is not None and not df_display_unfiltered.empty:
            try:
                df_display_unfiltered = custom_data_processing_hook(df_display_unfiltered, selected_foreign_key_ids)
                if df_display_unfiltered is None:
                     st.error(f"Falha no hook de processamento de dados para {entity_name_plural}.")
                     df_display_unfiltered = pd.DataFrame()
            except Exception as e:
                st.error(f"Erro no hook de processamento de dados para {entity_name_plural}: {e}")
                df_display_unfiltered = pd.DataFrame()
        if not df_display_unfiltered.empty:
            actual_cols_to_display = columns_to_display[:]
            if 'id' not in actual_cols_to_display and 'id' in df_display_unfiltered.columns:
                actual_cols_to_display.append('id')
            missing_cols = [col for col in actual_cols_to_display if col not in df_display_unfiltered.columns]
            for col in missing_cols:
                df_display_unfiltered[col] = None
            final_display_cols = [col for col in actual_cols_to_display if col in df_display_unfiltered.columns]
            df_display_unfiltered = df_display_unfiltered[final_display_cols].copy()
    df_filtered = display_search_box_and_filter_df(
        df_unfiltered=df_display_unfiltered if df_display_unfiltered is not None else pd.DataFrame(),
        search_columns=search_columns, search_key_suffix=key_suffix,
        entity_name_plural=entity_name_plural, search_label=custom_search_label
    )
    original_df_for_save = df_filtered.copy() if df_filtered is not None else pd.DataFrame()

    # df_filtered is the state of data after loading, (optional) custom processing, and search filtering.
    # This is the data that should be displayed in the editor.
    df_to_pass_to_editor = df_filtered if df_filtered is not None else pd.DataFrame()

    session_key_orig_df = f'{editor_key_suffix}_orig_df_for_autosave'

    if is_editable and auto_save:
        # Initialize session state for original DataFrame if not present or if data might have reloaded
        # A more robust reload detection might be needed if df_to_pass_to_editor can change identity
        # without other widget interactions causing a rerun.
        if session_key_orig_df not in st.session_state or not st.session_state[session_key_orig_df].shape == df_to_pass_to_editor.shape:
             # Basic check, might need refinement if df structure changes but data is same
            st.session_state[session_key_orig_df] = df_to_pass_to_editor.copy()

        # Ensure that df_to_pass_to_editor for the editor is actually the version from session state
        # if we expect it to be persistent across reruns before this point.
        # However, df_to_pass_to_editor is derived from upstream, so it *is* the current "original" for this render.
        # The session state one is the "previous original" to compare against for auto-save.

    edited_df = display_data_editor(
        df_to_edit=df_to_pass_to_editor, # Use the consistently prepared DataFrame
        column_config=column_config,
        editor_key_suffix=editor_key_suffix, # Use the specific editor_key_suffix
        is_editable=is_editable
    )

    if is_editable:
        if auto_save:
            previous_df_state = st.session_state.get(session_key_orig_df)
            # Make sure previous_df_state is not None and has 'id' if not empty, similar for edited_df
            can_compare = True
            if previous_df_state is None:
                can_compare = False
            if not previous_df_state.empty and 'id' not in previous_df_state.columns:
                 # This should not happen if load_and_prepare_data works correctly
                # st.warning(f"Auto-save: Previous state for {entity_name_plural} is missing 'id' column.")
                can_compare = False
            if not edited_df.empty and 'id' not in edited_df.columns:
                # This should not happen if display_data_editor's input had 'id'
                # st.warning(f"Auto-save: Edited data for {entity_name_plural} is missing 'id' column.")
                can_compare = False

            if can_compare and not edited_df.equals(previous_df_state):
                # original_df_for_save for auto-save should be the state *before* the current edit cycle began,
                # which is what we stored in session_state.
                if handle_save_changes(
                    original_df=previous_df_state, # Use the state from before this potential edit
                    edited_df=edited_df,
                    repository=repository,
                    entity_name_singular=entity_name_singular,
                    editable_columns=editable_columns,
                    required_fields=required_fields,
                    decimal_fields=decimal_fields,
                    special_conversions=special_conversions,
                    fields_to_remove_before_update=fields_to_remove_before_update
                ):
                    # If changes were successfully processed, update the stored "original" state
                    st.session_state[session_key_orig_df] = edited_df.copy()
                    st.rerun() # Rerun to reflect saved changes and clear editor's internal state
        else: # Manual save button
            # original_df_for_save is a fresh copy of df_filtered before editor display for this render cycle
            if st.button(f"Salvar Alterações em {entity_name_plural}", key=f"save_{key_suffix}"):
                if edited_df is not None: # edited_df can be None if df_to_pass_to_editor was None/empty
                    if handle_save_changes(
                        original_df=original_df_for_save, # Use df_filtered from current render cycle
                        edited_df=edited_df,
                        repository=repository,
                        entity_name_singular=entity_name_singular,
                        editable_columns=editable_columns,
                        required_fields=required_fields,
                        decimal_fields=decimal_fields,
                        special_conversions=special_conversions,
                        fields_to_remove_before_update=fields_to_remove_before_update
                    ):
                        # After manual save, update the session state if auto-save might be used later
                        # or if other parts of app rely on this session state.
                        # For now, let's assume manual save doesn't need to interact with session_key_orig_df
                        # unless auto_save can be dynamically toggled for the same component instance.
                        st.rerun()
                elif original_df_for_save.empty and (edited_df is None or edited_df.empty):
                     st.info(f"Nenhum dado para salvar em {entity_name_plural}.")
