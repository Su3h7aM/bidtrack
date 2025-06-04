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
    default_non_updatable = ['id', 'created_at', 'updated_at'] # These should not be in editable_columns
    if fields_to_remove_before_update is None:
        fields_to_remove = default_non_updatable
    else:
        fields_to_remove = list(set(default_non_updatable + fields_to_remove_before_update))

    changes_processed_any_row = False

    if original_df is None: # original_df is expected to be indexed by 'id'
        st.error(f"DataFrame original de {entity_name_singular} não fornecido. Impossível salvar.")
        return False
    if edited_df is None:
        st.info(f"Nenhum dado editado para {entity_name_singular.lower()}s.")
        return False

    if original_df.empty and edited_df.empty:
        st.info(f"Nenhum dado para salvar em {entity_name_singular.lower()}s.")
        return False

    # Assumption: original_df is already indexed by 'id' and contains all columns.
    # edited_df has a range index and contains only columns shown in the editor.
    # editable_columns should only contain columns that were actually in edited_df.

    if not original_df.index.name == 'id' and not original_df.empty :
        # This check is important. display_entity_management_ui must ensure original_df_for_save is indexed.
        st.error(f"DataFrame original de {entity_name_singular} não está indexado por 'id'. Falha interna.")
        # Attempt to index it now if 'id' column exists, otherwise fail.
        if 'id' in original_df.columns:
            original_df = original_df.set_index('id', drop=False)
            st.warning("Tentativa de reindexar DataFrame original bem-sucedida, mas isso deve ser feito pelo chamador.")
        else:
            st.error("DataFrame original não tem coluna 'id' para indexação. Impossível salvar.")
            return False

    # No new entities can be added via this save mechanism if they are not in original_df
    if not edited_df.empty and original_df.empty:
         new_rows_count = len(edited_df)
         if new_rows_count > 0:
            st.info(f"{new_rows_count} nova(s) linha(s) detectada(s) no editor. Esta função salva apenas alterações em linhas existentes. Use a funcionalidade de criação para novos {entity_name_singular.lower()}s.")
            # We might still process existing rows if any were somehow present in original_df and also in edited_df
            # but the current logic implies edited_df would be a subset of original_df rows.

    # Iterate through the edited_df (which has a range index)
    for edited_idx, edited_row_series in edited_df.iterrows():
        if edited_idx >= len(original_df.index):
            # This case implies more rows in edited_df than original_df, which means new rows.
            # These should be handled by an "add" mechanism, not "update".
            # For robustness, skip if editor somehow produces more rows than original.
            st.warning(f"Linha {edited_idx} no editor não corresponde a uma linha original. Pulando.")
            continue

        entity_id = original_df.index[edited_idx]

        # Check if this entity_id from original_df is valid (it should be, as it's from original_df's index)
        # No, this check is not needed: if entity_id is from original_df.index, it must be in original_df.index.
        # if entity_id not in original_df.index:
        #     st.warning(f"ID de entidade {entity_id} (da linha {edited_idx} do editor) não encontrado no DataFrame original. Pulando.")
        #     continue

        original_row_series = original_df.loc[entity_id]
        current_row_update_dict = {}
        row_had_actual_changes = False
        skip_this_row_due_to_error = False
        temp_changed_values_dict = {}
        for col_name_from_editor in editable_columns:
            # editable_columns should only contain columns that are in edited_row_series
            # and also intended to be editable (and thus should be in original_row_series too,
            # unless it's a new column concept not directly in the model but derived for editing).
            # For simplicity, assume editable_columns refers to fields in the model that are also in edited_row_series.
            if col_name_from_editor not in edited_row_series.index :
                # This column is in the editable_columns list but not in the edited DataFrame.
                # This might happen if editable_columns is not perfectly synced with df_for_editor_display.
                # The `actual_editable_columns_for_save` in `display_entity_management_ui` should prevent this.
                st.warning(f"Coluna '{col_name_from_editor}' definida como editável mas não encontrada nos dados editados para {entity_name_singular} ID {entity_id}. Pulando esta coluna.")
                continue

            # If col_name_from_editor is not in original_row_series, it implies it's a new, perhaps virtual, field.
            # The comparison logic needs to handle this. If it's truly new and not in the model,
            # it might only be used for special_conversions to target_fields that ARE in the model.
            original_value = original_row_series.get(col_name_from_editor) # Use .get() for safety
            edited_value = edited_row_series[col_name_from_editor]

            changed = False
            if original_value is None and pd.isna(edited_value): # original was None, editor set to NA (empty cell perhaps)
                 changed = False # Or True if None should be preserved explicitly. Depends on desired behavior for nulls.
            elif original_value is not None and pd.isna(edited_value): # original had value, editor cleared it
                 changed = True
            elif pd.isna(original_value) and not pd.isna(edited_value): # original was NA, editor provided value
                 changed = True
            elif pd.isna(original_value) and pd.isna(edited_value): # Both NA (e.g. np.nan, None, pd.NaT)
                 changed = False
            elif isinstance(original_value, pd.Timestamp) and isinstance(edited_value, pd.Timestamp):
                # Ensure Naive comparison if one is aware and other is naive
                ts_original = original_value.tz_localize(None) if original_value.tzinfo else original_value
                ts_edited = edited_value.tz_localize(None) if edited_value.tzinfo else edited_value
                changed = ts_original != ts_edited
            elif isinstance(original_value, pd.Timestamp) or isinstance(edited_value, pd.Timestamp): # Type mismatch involving Timestamp
                changed = True
            elif isinstance(original_value, Decimal):
                try:
                    str_edited_value = str(edited_value).strip()
                    if not str_edited_value and original_value is not None : changed = True # Cleared value
                    elif not str_edited_value and original_value is None: changed = False # Was None, remains effectively None
                    else: changed = original_value != Decimal(str_edited_value)
                except: changed = True # Conversion error implies change
            elif isinstance(edited_value, Decimal) and not isinstance(original_value, Decimal): # Original was not Decimal but edited is
                 try:
                    str_original_value = str(original_value).strip()
                    if not str_original_value and edited_value is not None: changed = True
                    elif not str_original_value and edited_value is None: changed = False
                    else: changed = Decimal(str_original_value) != edited_value
                 except: changed = True
            else: # General case
                # Try to compare types if possible, then values
                if type(original_value) != type(edited_value) and not (pd.isna(original_value) and pd.isna(edited_value)):
                    try:
                        # Attempt to cast edited_value to original_value's type for comparison
                        # This might not always be appropriate or possible
                        casted_edited_value = type(original_value)(edited_value)
                        changed = original_value != casted_edited_value
                    except (ValueError, TypeError):
                        changed = True # If casting fails, consider it a change
                else:
                    changed = original_value != edited_value

            if changed:
                temp_changed_values_dict[col_name_from_editor] = edited_value
                row_had_actual_changes = True
        if not row_had_actual_changes: continue
        changes_processed_any_row = True
        for col_name_from_editor, raw_edited_value in temp_changed_values_dict.items():
            target_field = col_name_from_editor # Default target is the same as editor column name
            try:
                if col_name_from_editor in special_conversions:
                    conv_details = special_conversions[col_name_from_editor]
                    target_field = conv_details["target_field"]
                    conversion_func = conv_details["conversion_func"]
                    current_row_update_dict[target_field] = conversion_func(raw_edited_value)
                else:
                    # If no special conversion, ensure the target_field (which is col_name_from_editor)
                    # is a valid field for the model (this check is implicitly done by SQLModel/Pydantic on update).
                    current_row_update_dict[target_field] = raw_edited_value
            except Exception as e:
                st.error(f"{entity_name_singular} ID {entity_id}: Erro ao converter '{col_name_from_editor}' ('{raw_edited_value}') para '{target_field}': {e}.")
                skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue

        # Required field validation: based on target_field names
        for req_field_target_name in required_fields:
            final_value_to_check = current_row_update_dict.get(req_field_target_name)

            # If the required field wasn't in temp_changed_values_dict (i.e., not edited),
            # its value would be the original one. But validation should be on the *new* state.
            # So, if it's not in current_row_update_dict, it means it wasn't changed OR it wasn't an editable column.
            # If it wasn't changed, its original value must have been valid.
            # If it IS in current_row_update_dict, we check its new value.
            if req_field_target_name in current_row_update_dict: # Check if it was part of the update
                 if final_value_to_check is None or (isinstance(final_value_to_check, str) and not final_value_to_check.strip()):
                    # Find the original editor column name for error message if special_conversion was used
                    editor_col_for_error = req_field_target_name
                    for cn_editor, conv_details in special_conversions.items():
                        if conv_details.get("target_field") == req_field_target_name:
                            editor_col_for_error = cn_editor; break
                    st.error(f"{entity_name_singular} ID {entity_id}: Campo obrigatório '{editor_col_for_error}' (destino: '{req_field_target_name}') está vazio ou inválido. Alterações não salvas para esta linha.")
                    skip_this_row_due_to_error = True; break
            # If a required_field is NOT in current_row_update_dict, it means it was not edited.
            # We assume its original value (from original_row_series) was valid.
            # If a required_field was NOT part of editable_columns, it could not have been changed.
            # This logic assumes required_fields are typically among editable_columns if they are to be enforced on edit.

        if skip_this_row_due_to_error: continue

        # Decimal field validation: based on target_field names
        for dec_field_target_name in decimal_fields:
            if dec_field_target_name in current_row_update_dict:
                val = current_row_update_dict[dec_field_target_name]
                if val is not None and not isinstance(val, Decimal):
                    try:
                        str_val = str(val).strip()
                        if not str_val: current_row_update_dict[dec_field_target_name] = None # Allow clearing optional decimal
                        else: current_row_update_dict[dec_field_target_name] = Decimal(str_val)
                    except Exception as e:
                        editor_col_for_error = dec_field_target_name
                        for cn_editor, conv_details in special_conversions.items():
                           if conv_details.get("target_field") == dec_field_target_name: editor_col_for_error = cn_editor; break
                        st.error(f"{entity_name_singular} ID {entity_id}: Valor inválido para campo decimal '{editor_col_for_error}' ('{val}'): {e}. Alterações não salvas para esta linha.")
                        skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue

        # Remove fields that should not go into the update payload (e.g., 'id', 'created_at', derived display fields)
        for field_to_rm in fields_to_remove: # fields_to_remove refers to target model field names
            current_row_update_dict.pop(field_to_rm, None)

        if not current_row_update_dict: # No actual changes to update after conversions and removals
            st.info(f"Nenhuma alteração real para {entity_name_singular} ID {entity_id} após processamento.")
            continue

        try:
            repository.update(entity_id, current_row_update_dict)
            st.success(f"{entity_name_singular} ID {entity_id} atualizado(a) com sucesso com: {current_row_update_dict}")
        except Exception as e:
            st.error(f"Falha ao salvar {entity_name_singular} ID {entity_id}: {e}. Tentativa de payload: {current_row_update_dict}")

    if not changes_processed_any_row:
        # This simple check replaces the more complex DataFrame comparison
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

    # Prepare original_df_for_save: ensure it's indexed by 'id'
    # This is the DataFrame that handle_save_changes will use as the source of truth for original values.
    # It must contain all original columns, including 'id', and be indexed by 'id'.
    original_df_for_save = pd.DataFrame()
    if df_filtered is not None and not df_filtered.empty:
        temp_original_df = df_filtered.copy()
        if 'id' in temp_original_df.columns:
            original_df_for_save = temp_original_df.set_index('id', drop=False)
        else:
            st.error(f"Erro crítico: DataFrame para {entity_name_plural} não possui coluna 'id' após o carregamento e filtragem. Edições não podem ser salvas.")
            # Fallback to an empty DataFrame with 'id' index if possible, or just empty.
            original_df_for_save = pd.DataFrame(columns=temp_original_df.columns).set_index('id', drop=False) if 'id' in temp_original_df.columns else pd.DataFrame()
    elif df_filtered is not None: # It's an empty DataFrame
        original_df_for_save = pd.DataFrame(columns=df_filtered.columns)
        if 'id' in original_df_for_save.columns:
            original_df_for_save = original_df_for_save.set_index('id', drop=False)
        # else: it remains an empty DataFrame, possibly without 'id' if df_filtered was truly empty and schema-less

    # This df_filtered contains all columns, including 'id'.
    # original_df_for_save is a copy of this, used by handle_save_changes. It will be indexed by 'id'.

    # Part 1: Modify display_entity_management_ui (Column Hiding Strategy)
    df_full_data = df_filtered if df_filtered is not None else pd.DataFrame()

    final_column_config_for_editor = {}
    if not df_full_data.empty:
        for col_name in df_full_data.columns:
            if col_name in columns_to_display:
                final_column_config_for_editor[col_name] = column_config.get(col_name)
            else:
                final_column_config_for_editor[col_name] = None # Hide column
    else: # df_full_data is empty, use original column_config
        final_column_config_for_editor = column_config.copy()

    session_key_orig_df = f'{editor_key_suffix}_orig_df_for_autosave'

    if is_editable and auto_save:
        # For auto-save, the comparison df (previous_df_state) should match the structure of
        # what edited_df_output will be (all columns, range index).
        # So, st.session_state[session_key_orig_df] should store df_full_data.copy()
        if session_key_orig_df not in st.session_state or \
           not st.session_state[session_key_orig_df].equals(df_full_data): # More robust check
            st.session_state[session_key_orig_df] = df_full_data.copy()

    # display_data_editor is called with df_full_data.
    # Its output, edited_df_output, will have all columns from df_full_data.
    # display_data_editor uses hide_index=True, so edited_df_output has a range index.
    edited_df_output = display_data_editor(
        df_to_edit=df_full_data,
        column_config=final_column_config_for_editor,
        editor_key_suffix=editor_key_suffix,
        is_editable=is_editable
    )

    if is_editable:
        if auto_save:
            previous_df_state_for_autosave = st.session_state.get(session_key_orig_df) # This is full data

            if previous_df_state_for_autosave is not None and \
               not edited_df_output.equals(previous_df_state_for_autosave):

                # editable_columns is from tab_content files, refers to user-editable fields.
                # These fields must be in columns_to_display.
                actual_editable_columns = [
                    col for col in editable_columns if col in columns_to_display and col in df_full_data.columns
                ]
                if handle_save_changes( # handle_save_changes expects original_df_for_save (indexed)
                                        # and edited_df_output (range index, all columns, including 'id')
                    original_df=original_df_for_save,
                    edited_df=edited_df_output,
                    repository=repository,
                    entity_name_singular=entity_name_singular,
                    editable_columns=actual_editable_columns,
                    required_fields=required_fields,
                    decimal_fields=decimal_fields,
                    special_conversions=special_conversions,
                    fields_to_remove_before_update=fields_to_remove_before_update
                ):
                    st.session_state[session_key_orig_df] = edited_df_output.copy() # Update session state with new full data
                    st.rerun()
        else: # Manual save button
            if st.button(f"Salvar Alterações em {entity_name_plural}", key=f"save_{key_suffix}"):
                if edited_df_output is not None:
                    actual_editable_columns = [
                        col for col in editable_columns if col in columns_to_display and col in df_full_data.columns
                    ]
                    if handle_save_changes(
                        original_df=original_df_for_save,
                        edited_df=edited_df_output,
                        repository=repository,
                        entity_name_singular=entity_name_singular,
                        editable_columns=actual_editable_columns,
                        required_fields=required_fields,
                        decimal_fields=decimal_fields,
                        special_conversions=special_conversions,
                        fields_to_remove_before_update=fields_to_remove_before_update
                    ):
                        st.rerun()
                elif original_df_for_save.empty and (edited_df_output is None or edited_df_output.empty):
                     st.info(f"Nenhum dado para salvar em {entity_name_plural}.")
