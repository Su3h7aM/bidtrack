import streamlit as st
import pandas as pd
from decimal import Decimal # Required for quote fields
from db.models import BiddingMode # Required for mode handling
from ui.utils import get_options_map # For Licitação selection
from services.dataframes import get_quotes_dataframe # To get calculated_price logic easily

# Helper function to load and prepare data for tabs
def load_and_prepare_data(repository, entity_name: str):
    """
    Loads data from the given repository, prepares it, and handles errors.

    Args:
        repository: The repository instance to fetch data from.
        entity_name (str): The name of the entity being loaded (e.g., "Licitações")
                           for use in messages.

    Returns:
        pd.DataFrame or None: Processed DataFrame if successful, else None.
    """
    try:
        data_list = repository.get_all()
    except Exception as e:
        st.error(f"Erro ao carregar dados de {entity_name}: {e}")
        return None

    if not data_list:
        st.info(f"Nenhum(a) {entity_name.lower()} cadastrado(a).")
        return None

    try:
        df = pd.DataFrame([item.model_dump() for item in data_list])
    except Exception as e:
        st.error(f"Erro ao converter dados de {entity_name} para DataFrame: {e}")
        return None

    # Basic DataFrame preparation
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')
    if "updated_at" in df.columns:
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors='coerce')
    
    return df

# Helper function for search box and filtering
def display_search_box_and_filter_df(df_unfiltered: pd.DataFrame, search_columns: list[str], search_key_suffix: str, entity_name_plural: str, search_label: str = None):
    """
    Displays a search box and filters a DataFrame based on the input.

    Args:
        df_unfiltered (pd.DataFrame): The original, unfiltered DataFrame.
        search_columns (list[str]): List of column names to search within.
        search_key_suffix (str): A unique suffix for the st.text_input key.
        entity_name_plural (str): Plural name of the entity for messages (e.g., "Licitações").
        search_label (str, optional): Custom label for the search box. If None, a default is used.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    if search_label is None:
        search_label = f"Buscar em {entity_name_plural} (por {', '.join(search_columns)}):"

    search_term = st.text_input(
        search_label,
        key=f"search_{search_key_suffix}"
    )

    if not search_term:
        return df_unfiltered

    search_term_lower = search_term.lower()
    
    combined_filter = pd.Series([False] * len(df_unfiltered), index=df_unfiltered.index)

    for col in search_columns:
        if col in df_unfiltered.columns:
            combined_filter |= df_unfiltered[col].astype(str).str.lower().str.contains(search_term_lower, na=False)
        else:
            # st.warning(f"Search column '{col}' not found in DataFrame for {entity_name_plural}.")
            pass # Optionally log or handle missing columns

    df_filtered = df_unfiltered[combined_filter]

    if df_filtered.empty and not df_unfiltered.empty and search_term: # ensure search_term is not empty
        st.info(f"Nenhum resultado encontrado para sua busca em {entity_name_plural}.")
    
    return df_filtered

# Helper function to display the data editor
def display_data_editor(df_to_edit: pd.DataFrame, column_config: dict, editor_key_suffix: str):
    """
    Displays the st.data_editor component.

    Args:
        df_to_edit (pd.DataFrame): The DataFrame to be edited.
        column_config (dict): Configuration for the data editor columns.
        editor_key_suffix (str): A unique suffix for the st.data_editor key.

    Returns:
        pd.DataFrame: The edited DataFrame.
    """
    edited_df = st.data_editor(
        df_to_edit,
        key=f"editor_{editor_key_suffix}",
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True
    )
    return edited_df

# Helper function to handle saving changes
def handle_save_changes(
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame,
    repository, # Actual repository instance
    entity_name_singular: str,
    editable_columns: list[str],
    required_fields: list[str] = None,
    decimal_fields: list[str] = None,
    special_conversions: dict = None, # e.g., {"mode_display": {"target_field": "mode", "conversion_func": BiddingMode}}
    fields_to_remove_before_update: list[str] = None
):
    """
    Handles the logic for saving changes made in st.data_editor.

    Args:
        original_df (pd.DataFrame): DataFrame before editing.
        edited_df (pd.DataFrame): DataFrame after editing.
        repository: The repository instance for the entity.
        entity_name_singular (str): Singular name of the entity (e.g., "Licitação").
        editable_columns (list[str]): Columns that are editable and should be checked.
        required_fields (list[str], optional): Fields that cannot be empty/None. Defaults to an empty list.
        decimal_fields (list[str], optional): Fields to convert to Decimal. Defaults to an empty list.
        special_conversions (dict, optional): Handles special conversions. 
                                            Example: {"original_col": {"target_field": "final_col", "conversion_func": lambda x: ConvertedValue(x)}}
                                            The key is the column name from the edited_df.
                                            'target_field' is the name of the field to be saved in the database.
                                            'conversion_func' is the function to apply to the value.
        fields_to_remove_before_update (list[str], optional): Fields to remove from update_dict before saving. 
                                                            Defaults to ['id', 'created_at', 'updated_at']. Additional fields
                                                            that are purely for display (e.g., derived names) should also be added here
                                                            if they are part of `editable_columns` or generated during processing
                                                            but not actual model fields.

    Returns:
        bool: True if any changes were processed and attempted to save, False otherwise.
    """
    if required_fields is None:
        required_fields = []
    if decimal_fields is None:
        decimal_fields = []
    if special_conversions is None:
        special_conversions = {}
    if fields_to_remove_before_update is None:
        # Default fields that are usually not updatable directly or are managed by the ORM/database
        default_non_updatable = ['id', 'created_at', 'updated_at']
    else:
        default_non_updatable = ['id', 'created_at', 'updated_at'] + [f for f in fields_to_remove_before_update if f not in ['id', 'created_at', 'updated_at']]
    
    fields_to_remove = list(set(default_non_updatable)) # Ensure uniqueness

    changes_processed_any_row = False
    
    if 'id' not in original_df.columns or 'id' not in edited_df.columns:
        st.error(f"Coluna 'id' não encontrada nos DataFrames para {entity_name_singular}. Não é possível salvar alterações.")
        return False
        
    original_df_indexed = original_df.set_index('id', drop=False)
    edited_df_indexed = edited_df.set_index('id', drop=False)

    for entity_id, edited_row_series in edited_df_indexed.iterrows():
        if entity_id not in original_df_indexed.index:
            # st.warning(f"{entity_name_singular} com ID {entity_id} é novo(a) e será ignorado(a) pela função de atualização.")
            continue

        original_row_series = original_df_indexed.loc[entity_id]
        current_row_update_dict = {} # Stores changes for the current row, using actual target field names
        row_had_actual_changes = False 
        skip_this_row_due_to_error = False

        # Step 1: Identify changes and populate initial update_dict with raw edited values
        temp_changed_values_dict = {} # Holds column_name_from_editor: new_value
        for col_name_from_editor in editable_columns:
            if col_name_from_editor not in edited_row_series.index or col_name_from_editor not in original_row_series.index:
                # This case should ideally not happen if inputs are correct
                # st.warning(f"Coluna editável '{col_name_from_editor}' ausente nos dados para ID {entity_id}.")
                continue

            original_value = original_row_series[col_name_from_editor]
            edited_value = edited_row_series[col_name_from_editor]

            changed = False
            if pd.isna(original_value) and pd.isna(edited_value):
                changed = False
            elif pd.isna(original_value) or pd.isna(edited_value): # One is NaN, other is not
                changed = True
            # Datetime comparison (assuming pd.Timestamp objects)
            elif isinstance(original_value, pd.Timestamp) and isinstance(edited_value, pd.Timestamp):
                # NaT comparison already handled by pd.isna
                if original_value.tzinfo != edited_value.tzinfo: # Timezone mismatch
                    # Attempt to make them comparable, e.g., by converting both to UTC
                    # This is a simplistic approach; robust timezone handling can be complex
                    try:
                        changed = original_value.tz_convert('UTC') != edited_value.tz_convert('UTC')
                    except TypeError: # One might be naive and the other aware
                        changed = True # Treat as changed if they can't be reliably compared
                else: # Same timezone or both naive
                    changed = original_value != edited_value
            elif isinstance(original_value, pd.Timestamp) or isinstance(edited_value, pd.Timestamp): # One is datetime, other is not
                changed = True # Types are different
            # Decimal comparison (original might be Decimal, edited might be float/str from data_editor)
            elif isinstance(original_value, Decimal):
                try:
                    changed = original_value != Decimal(str(edited_value))
                except: # Conversion of edited_value to Decimal failed
                    changed = True 
            # General comparison (includes str, int, float if not Decimal, bool)
            else:
                # For floats, direct comparison is often okay, but for values from UI, stringify can be safer
                if type(original_value) != type(edited_value) and not (pd.isna(original_value) or pd.isna(edited_value)):
                    # Attempt to cast edited_value to original_value's type if simple (e.g. int vs float)
                    try:
                        casted_edited_value = type(original_value)(edited_value)
                        changed = original_value != casted_edited_value
                    except (ValueError, TypeError):
                        changed = True # Types are fundamentally different or conversion failed
                else:
                    changed = original_value != edited_value
            
            if changed:
                temp_changed_values_dict[col_name_from_editor] = edited_value
                row_had_actual_changes = True
        
        if not row_had_actual_changes:
            continue # No changes in this row based on editable_columns

        changes_processed_any_row = True # Mark that we are processing at least one row

        # Step 2: Apply special conversions and build the current_row_update_dict
        # This dict will use target field names.
        for col_name_from_editor, raw_edited_value in temp_changed_values_dict.items():
            if col_name_from_editor in special_conversions:
                conv_details = special_conversions[col_name_from_editor]
                target_field = conv_details["target_field"]
                conversion_func = conv_details["conversion_func"]
                try:
                    current_row_update_dict[target_field] = conversion_func(raw_edited_value)
                except Exception as e:
                    st.error(f"{entity_name_singular} ID {entity_id}: Erro ao converter '{col_name_from_editor}' ('{raw_edited_value}') para '{target_field}': {e}.")
                    skip_this_row_due_to_error = True; break
            else:
                # If no special conversion, the target field name is the same as editor column name
                current_row_update_dict[col_name_from_editor] = raw_edited_value
        if skip_this_row_due_to_error: continue

        # Step 3: Validate required fields (using target field names in current_row_update_dict or original if not changed)
        for req_field_target_name in required_fields:
            # Value could be in current_row_update_dict if changed, or directly from edited_row_series if not changed but still needs validation
            value_to_check = current_row_update_dict.get(req_field_target_name, edited_row_series.get(req_field_target_name))
            
            if value_to_check is None or (isinstance(value_to_check, str) and not value_to_check.strip()):
                # Find which editor column corresponds to this target name for a better error message
                editor_col_for_error = req_field_target_name
                for cn_editor, conv_details in special_conversions.items():
                    if conv_details["target_field"] == req_field_target_name:
                        editor_col_for_error = cn_editor; break
                st.error(f"{entity_name_singular} ID {entity_id}: Campo obrigatório '{editor_col_for_error}' (destino: '{req_field_target_name}') está vazio. Alterações não salvas.")
                skip_this_row_due_to_error = True; break
        if skip_this_row_due_to_error: continue

        # Step 4: Decimal conversions (using target field names in current_row_update_dict)
        for dec_field_target_name in decimal_fields:
            if dec_field_target_name in current_row_update_dict: # Only process if it's part of changed values
                val = current_row_update_dict[dec_field_target_name]
                if val is not None and not isinstance(val, Decimal):
                    try:
                        if isinstance(val, str) and not val.strip(): # Empty string for optional decimal
                            current_row_update_dict[dec_field_target_name] = None 
                        else:
                            current_row_update_dict[dec_field_target_name] = Decimal(str(val))
                    except Exception as e:
                        editor_col_for_error = dec_field_target_name # Fallback error reporting
                        for cn_editor, conv_details in special_conversions.items():
                           if conv_details.get("target_field") == dec_field_target_name: editor_col_for_error = cn_editor; break
                        st.error(f"{entity_name_singular} ID {entity_id}: Valor inválido para campo decimal '{editor_col_for_error}' ('{val}'): {e}.")
                        skip_this_row_due_to_error = True; break
            # If an optional decimal field was cleared (now None), and it's in current_row_update_dict as None, that's fine.
            # If it was required, it would have been caught by required_fields check.
        if skip_this_row_due_to_error: continue
        
        # Step 5: Remove non-updatable fields from the final payload
        for field_to_rm in fields_to_remove:
            current_row_update_dict.pop(field_to_rm, None)
        
        if not current_row_update_dict: # No changes left after processing
            continue

        # Step 6: Call repository update
        try:
            # Ensure entity_id is of the correct type for the repository (usually int or UUID)
            # The index entity_id should already be of the correct type if DataFrame was formed correctly.
            repository.update(entity_id, current_row_update_dict)
            st.success(f"{entity_name_singular} ID {entity_id} atualizado(a) com sucesso.")
            # Optionally show changes: f" com: {current_row_update_dict}"
        except Exception as e:
            st.error(f"Falha ao salvar {entity_name_singular} ID {entity_id}: {e}. Tentativa de payload: {current_row_update_dict}")
            # No changes_processed_any_row = True here because save failed

    if not changes_processed_any_row:
         # Check if dataframes were identical to begin with, considering only common columns
        common_cols = original_df_indexed.columns.intersection(edited_df_indexed.columns)
        if original_df_indexed[common_cols].equals(edited_df_indexed[common_cols]):
            st.info(f"Nenhuma alteração detectada para salvar em {entity_name_singular.lower()}s.")
        # else: implies some edits were made but then reverted or failed validation leading to no repo calls.
        # The individual error messages for rows should cover this.
        
    return changes_processed_any_row # True if any row had changes and an update attempt was made (even if it failed)

def show_management_tables_view(bidding_repo, item_repo, supplier_repo, quote_repo, bidder_repo, bid_repo):
    """
    Displays the management tables page with different tabs for each entity.
    """
    st.title("Gerenciamento de Tabelas")

    tab_labels = [
        "Licitações",
        "Itens",
        "Fornecedores",
        "Orçamentos",
        "Licitantes",
        "Lances",
    ]
    
    tab_biddings, tab_items, tab_suppliers, tab_quotes, tab_bidders, tab_bids = st.tabs(tab_labels)

    with tab_biddings:
        st.subheader("Gerenciar Licitações")
        df_biddings_raw = load_and_prepare_data(bidding_repo, "Licitações")

        if df_biddings_raw is not None and not df_biddings_raw.empty:
            # Tab-specific DataFrame preparations
            if "mode" in df_biddings_raw.columns:
                df_biddings_raw["mode_display"] = df_biddings_raw["mode"].apply(
                    lambda x: x.value if isinstance(x, BiddingMode) else x
                )
            else:
                df_biddings_raw["mode_display"] = None # Or some default if mode is missing

            if "date" in df_biddings_raw.columns:
                df_biddings_raw["date"] = pd.to_datetime(df_biddings_raw["date"], errors='coerce')
            else:
                df_biddings_raw["date"] = None


            cols_to_display_biddings = ["id", "process_number", "city", "mode_display", "date", "description", "status", "created_at", "updated_at"]
            for col in cols_to_display_biddings:
                if col not in df_biddings_raw.columns:
                    df_biddings_raw[col] = None 
            
            df_display_biddings_unfiltered = df_biddings_raw[cols_to_display_biddings].copy()

            search_columns_biddings = ["process_number", "city", "mode_display"]
            df_filtered_biddings = display_search_box_and_filter_df(
                df_unfiltered=df_display_biddings_unfiltered,
                search_columns=search_columns_biddings,
                search_key_suffix="biddings_tab",
                entity_name_plural="Licitações",
                search_label="Buscar Licitações (por nº processo, cidade, modo):"
            )

            column_config_biddings = {
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "process_number": st.column_config.TextColumn("Nº do Processo", required=True),
                "city": st.column_config.TextColumn("Cidade", required=True),
                "mode_display": st.column_config.SelectboxColumn(
                    "Modalidade", 
                    options=[mode.value for mode in BiddingMode],
                    required=True
                ),
                "date": st.column_config.DatetimeColumn("Data", format="YYYY-MM-DD HH:mm", required=True), # Ensure this format is consistent
                "description": st.column_config.TextColumn("Descrição"),
                "status": st.column_config.TextColumn("Status"), 
                "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
            }
            
            original_df_for_save_biddings = df_filtered_biddings.copy()

            edited_biddings_df = display_data_editor(
                df_to_edit=df_filtered_biddings,
                column_config=column_config_biddings,
                editor_key_suffix="biddings_tab"
            )

            if st.button("Salvar Alterações em Licitações", key="save_biddings_tab"):
                editable_cols_biddings = ["process_number", "city", "mode_display", "date", "description", "status"]
                required_cols_biddings = ["process_number", "city", "mode_display", "date"]
                
                special_conversions_biddings = {
                    "mode_display": {"target_field": "mode", "conversion_func": BiddingMode},
                    "date": {"target_field": "date", "conversion_func": lambda x: pd.to_datetime(x, errors='coerce')} 
                }
                # mode_display itself should be removed as it's not a direct model field.
                # date is converted, so original 'date' (if string from editor) is fine to be replaced by converted 'date'
                fields_to_remove_biddings = ["mode_display"] 

                if handle_save_changes(
                    original_df=original_df_for_save_biddings,
                    edited_df=edited_biddings_df,
                    repository=bidding_repo,
                    entity_name_singular="Licitação",
                    editable_columns=editable_cols_biddings,
                    required_fields=required_cols_biddings,
                    special_conversions=special_conversions_biddings,
                    fields_to_remove_before_update=fields_to_remove_biddings 
                ):
                    st.rerun()
        # else: load_and_prepare_data already showed messages for None or empty

    with tab_items:
        st.subheader("Gerenciar Itens")
        
        # Step 1: Select Bidding
        # This part remains specific as it drives the item display
        all_biddings_for_item_tab = None
        try:
            all_biddings_for_item_tab = bidding_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar Licitações para seleção: {e}")
            # return # Or allow to proceed if items can be shown without bidding context initially
        
        if not all_biddings_for_item_tab:
            st.info("Nenhuma licitação cadastrada para selecionar e listar itens.")
            # return # Stop if no biddings to select from
        else:
            bidding_options_map, bidding_option_ids = get_options_map(
                data_list=all_biddings_for_item_tab,
                extra_cols=["city", "process_number", "mode_value"],
                default_message="Selecione uma Licitação para ver seus itens...",
            )
            selected_bidding_id_for_items = st.selectbox(
                "Escolha uma Licitação para gerenciar seus itens:",
                options=bidding_option_ids,
                format_func=lambda x: bidding_options_map.get(x, "Selecione..."),
                key="select_bidding_for_items_tab",
            )

            if selected_bidding_id_for_items is None:
                st.info("Por favor, selecione uma licitação para ver os itens.")
            else:
                # Step 2: Load Item Data (all items, then filter)
                df_all_items_raw = load_and_prepare_data(item_repo, "Itens")

                if df_all_items_raw is not None: # Not necessarily empty yet, could be empty after filtering
                    # Filter items for the selected bidding
                    df_items_for_selected_bidding = df_all_items_raw[
                        df_all_items_raw["bidding_id"] == selected_bidding_id_for_items
                    ].copy() # Use .copy() to avoid SettingWithCopyWarning later

                    if df_items_for_selected_bidding.empty:
                        st.info("Nenhum item cadastrado para esta licitação.")
                    else:
                        # Step 3: Prepare Display DF
                        cols_to_display_items = ["id", "name", "description", "code", "quantity", "unit", "bidding_id", "created_at", "updated_at"]
                        for col in cols_to_display_items:
                            if col not in df_items_for_selected_bidding.columns:
                                df_items_for_selected_bidding[col] = None
                        
                        df_display_items_unfiltered = df_items_for_selected_bidding[cols_to_display_items].copy()

                        # Step 4: Search
                        search_columns_items = ["name", "description", "code"]
                        df_filtered_items = display_search_box_and_filter_df(
                            df_unfiltered=df_display_items_unfiltered,
                            search_columns=search_columns_items,
                            search_key_suffix="items_tab",
                            entity_name_plural="Itens",
                            search_label="Buscar Itens (por nome, descrição, código):"
                        )

                        # Step 5: Data Editor
                        column_config_items = {
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "name": st.column_config.TextColumn("Nome do Item", required=True),
                            "description": st.column_config.TextColumn("Descrição do Item"),
                            "code": st.column_config.TextColumn("Código do Item"),
                            "quantity": st.column_config.NumberColumn("Quantidade", format="%.2f", min_value=0.00, required=True), # Allow 0? min_value=0.01 in original
                            "unit": st.column_config.TextColumn("Unidade", required=True),
                            "bidding_id": st.column_config.NumberColumn("ID da Licitação", disabled=True),
                            "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                            "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
                        }
                        
                        original_df_for_save_items = df_filtered_items.copy()

                        edited_items_df = display_data_editor(
                            df_to_edit=df_filtered_items,
                            column_config=column_config_items,
                            editor_key_suffix="items_tab"
                        )

                        # Step 6: Save Changes
                        if st.button("Salvar Alterações em Itens", key="save_items_tab"):
                            editable_cols_items = ["name", "description", "code", "quantity", "unit"]
                            required_cols_items = ["name", "quantity", "unit"]
                            # Assuming 'quantity' is float/numeric in the model, not strict Decimal from db.
                            # `handle_save_changes` will compare them appropriately.
                            # If it must be Decimal, then add "quantity" to decimal_fields.
                            
                            # `bidding_id` is not editable here. It's fixed by the selection.
                            fields_to_remove_items = ["bidding_id"]


                            # Special handling for quantity if it needs to be float and positive
                            # This kind of specific validation might be better inside a custom validation function passed to handle_save_changes
                            # For now, let's assume handle_save_changes's general Decimal/float handling is okay.
                            # The original code had a specific check:
                            # if 'quantity' in item_update_dict:
                            #     item_update_dict['quantity'] = float(item_update_dict['quantity'])
                            #     if item_update_dict['quantity'] <= 0: error...
                            # This logic would need to be adapted if passed as a conversion/validation to the generic saver.
                            # For now, relying on `min_value` in NumberColumn and `required`.

                            if handle_save_changes(
                                original_df=original_df_for_save_items,
                                edited_df=edited_items_df,
                                repository=item_repo,
                                entity_name_singular="Item",
                                editable_columns=editable_cols_items,
                                required_fields=required_cols_items,
                                fields_to_remove_before_update=fields_to_remove_items
                                # decimal_fields=["quantity"] # if strict Decimal needed for repo
                            ):
                                st.rerun()
                # else: load_and_prepare_data (for all_items_df) already showed messages if it failed at that stage

    with tab_suppliers:
        st.subheader("Gerenciar Fornecedores")
        
        df_suppliers_raw = load_and_prepare_data(supplier_repo, "Fornecedores")

        if df_suppliers_raw is not None and not df_suppliers_raw.empty:
            cols_to_display_suppliers = ["id", "name", "website", "email", "phone", "desc", "created_at", "updated_at"]
            # Ensure all display columns exist, adding missing ones with None
            for col in cols_to_display_suppliers:
                if col not in df_suppliers_raw.columns:
                    df_suppliers_raw[col] = None
            
            df_display_suppliers_unfiltered = df_suppliers_raw[cols_to_display_suppliers].copy()

            search_columns_suppliers = ["name", "website", "email", "phone", "desc"]
            df_filtered_suppliers = display_search_box_and_filter_df(
                df_unfiltered=df_display_suppliers_unfiltered,
                search_columns=search_columns_suppliers,
                search_key_suffix="suppliers_tab",
                entity_name_plural="Fornecedores",
                search_label="Buscar Fornecedores (por nome, website, email, etc.):"
            )

            column_config_suppliers = {
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Nome", required=True),
                "website": st.column_config.TextColumn("Website"),
                "email": st.column_config.TextColumn("Email"),
                "phone": st.column_config.TextColumn("Telefone"),
                "desc": st.column_config.TextColumn("Descrição"), # Model field is 'desc'
                "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
            }

            # Make a copy of the filtered DataFrame to pass as original_df to handle_save_changes
            # This ensures that we compare against the data that was actually shown in the editor before edits
            original_df_for_save_suppliers = df_filtered_suppliers.copy()

            edited_suppliers_df = display_data_editor(
                df_to_edit=df_filtered_suppliers, # Pass the filtered (but not yet edited by user in this run) df
                column_config=column_config_suppliers,
                editor_key_suffix="suppliers_tab"
            )

            if st.button("Salvar Alterações em Fornecedores", key="save_suppliers_tab"):
                editable_cols_suppliers = ["name", "website", "email", "phone", "desc"]
                required_cols_suppliers = ["name"]
                
                # Fields to remove: default ones + any display-only if they were in editable_cols_suppliers
                # (currently 'desc' is the actual model field name, so no extra here)

                if handle_save_changes(
                    original_df=original_df_for_save_suppliers, # The state of data before this specific edit session
                    edited_df=edited_suppliers_df,
                    repository=supplier_repo,
                    entity_name_singular="Fornecedor",
                    editable_columns=editable_cols_suppliers,
                    required_fields=required_cols_suppliers,
                    # decimal_fields=[], # No decimal fields for suppliers
                    # special_conversions={}, # No special conversions for suppliers
                    # fields_to_remove_before_update=[] # Defaults are 'id', 'created_at', 'updated_at'
                ):
                    st.rerun()
        # else: load_and_prepare_data already showed messages for None or empty

    with tab_quotes:
        st.subheader("Gerenciar Orçamentos")
        
        # Step 1: Load raw data lists
        quotes_list_raw = None
        items_list_for_quotes_map = {}
        suppliers_list_for_quotes_map = {}
        error_loading_essential_data = False

        try:
            quotes_list_raw = quote_repo.get_all()
            items_list = item_repo.get_all()
            suppliers_list = supplier_repo.get_all()
            
            if items_list:
                items_list_for_quotes_map = {item.id: item.name for item in items_list}
            if suppliers_list:
                suppliers_list_for_quotes_map = {supplier.id: supplier.name for supplier in suppliers_list}

        except Exception as e:
            st.error(f"Erro ao carregar dados brutos para Orçamentos: {e}")
            error_loading_essential_data = True

        if not error_loading_essential_data:
            if not quotes_list_raw:
                st.info("Nenhum orçamento cadastrado.")
            else:
                # Step 2: Build Initial DataFrame for display
                quotes_data_for_display = []
                for quote in quotes_list_raw:
                    supplier_name = suppliers_list_for_quotes_map.get(quote.supplier_id, "N/A")
                    item_name = items_list_for_quotes_map.get(quote.item_id, "N/A")
                    
                    base_price = Decimal(str(quote.price)) if quote.price is not None else Decimal(0)
                    freight = Decimal(str(quote.freight)) if quote.freight is not None else Decimal(0)
                    additional_costs = Decimal(str(quote.additional_costs)) if quote.additional_costs is not None else Decimal(0)
                    taxes_percentage = Decimal(str(quote.taxes)) if quote.taxes is not None else Decimal(0)
                    margin_percentage = Decimal(str(quote.margin)) if quote.margin is not None else Decimal(0)
                    
                    price_with_freight_costs = base_price + freight + additional_costs
                    taxes_value = price_with_freight_costs * (taxes_percentage / Decimal(100))
                    price_before_margin = price_with_freight_costs + taxes_value
                    margin_value = price_before_margin * (margin_percentage / Decimal(100))
                    calculated_price = price_before_margin + margin_value

                    quotes_data_for_display.append({
                        "id": quote.id,
                        "item_name": item_name,
                        "supplier_name": supplier_name,
                        "price": quote.price, # Base cost
                        "freight": quote.freight,
                        "additional_costs": quote.additional_costs,
                        "taxes": quote.taxes, # Percentage
                        "margin": quote.margin, # Percentage
                        "calculated_price": calculated_price,
                        "notes": quote.notes,
                        "item_id": quote.item_id,
                        "supplier_id": quote.supplier_id,
                        "created_at": quote.created_at,
                        "updated_at": quote.updated_at,
                    })
                
                df_quotes_built = pd.DataFrame(quotes_data_for_display)
                if "created_at" in df_quotes_built.columns:
                    df_quotes_built["created_at"] = pd.to_datetime(df_quotes_built["created_at"], errors='coerce')
                if "updated_at" in df_quotes_built.columns:
                    df_quotes_built["updated_at"] = pd.to_datetime(df_quotes_built["updated_at"], errors='coerce')

                # Step 3: Define display columns and ensure they exist
                cols_to_display_quotes = [
                    "id", "item_name", "supplier_name", "price", "freight", "additional_costs", 
                    "taxes", "margin", "calculated_price", "notes", "item_id", "supplier_id", 
                    "created_at", "updated_at"
                ]
                for col in cols_to_display_quotes:
                    if col not in df_quotes_built.columns:
                        df_quotes_built[col] = None # Add if missing, though builder should include them
                
                df_display_quotes_unfiltered = df_quotes_built[cols_to_display_quotes].copy()
                
                # Step 4: Search
                search_columns_quotes = ["item_name", "supplier_name", "notes"]
                df_filtered_quotes = display_search_box_and_filter_df(
                    df_unfiltered=df_display_quotes_unfiltered,
                    search_columns=search_columns_quotes,
                    search_key_suffix="quotes_tab",
                    entity_name_plural="Orçamentos",
                    search_label="Buscar Orçamentos (por item, fornecedor, notas):"
                )

                # Step 5: Data Editor
                column_config_quotes = {
                    "id": st.column_config.NumberColumn("ID Orçamento", disabled=True),
                    "item_name": st.column_config.TextColumn("Item", disabled=True),
                    "supplier_name": st.column_config.TextColumn("Fornecedor", disabled=True),
                    "price": st.column_config.NumberColumn("Preço Base (Custo)", format="R$ %.2f", required=True, help="Custo base do produto/serviço."),
                    "freight": st.column_config.NumberColumn("Frete (R$)", format="R$ %.2f", required=False),
                    "additional_costs": st.column_config.NumberColumn("Custos Adic. (R$)", format="R$ %.2f", required=False),
                    "taxes": st.column_config.NumberColumn("Impostos (%)", format="%.2f", help="Ex: 6 para 6%", required=False),
                    "margin": st.column_config.NumberColumn("Margem (%)", format="%.2f", help="Ex: 20 para 20%", required=True),
                    "calculated_price": st.column_config.NumberColumn("Preço Calculado", format="R$ %.2f", disabled=True),
                    "notes": st.column_config.TextColumn("Notas"),
                    "item_id": st.column_config.NumberColumn("ID Item", disabled=True),
                    "supplier_id": st.column_config.NumberColumn("ID Fornecedor", disabled=True),
                    "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                    "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
                }
                
                original_df_for_save_quotes = df_filtered_quotes.copy()

                edited_quotes_df = display_data_editor(
                    df_to_edit=df_filtered_quotes,
                    column_config=column_config_quotes,
                    editor_key_suffix="quotes_tab"
                )

                # Step 6: Save Changes
                if st.button("Salvar Alterações em Orçamentos", key="save_quotes_tab"):
                    editable_cols_quotes = ["price", "freight", "additional_costs", "taxes", "margin", "notes"]
                    required_cols_quotes = ["price", "margin"] # item_id, supplier_id are inherent
                    decimal_cols_quotes = ["price", "freight", "additional_costs", "taxes", "margin"]
                    
                    fields_to_remove_quotes = [
                        'item_name', 'supplier_name', 'calculated_price', 'item_id', 'supplier_id'
                    ] # id, created_at, updated_at are removed by default in handle_save_changes

                    if handle_save_changes(
                        original_df=original_df_for_save_quotes,
                        edited_df=edited_quotes_df,
                        repository=quote_repo,
                        entity_name_singular="Orçamento",
                        editable_columns=editable_cols_quotes,
                        required_fields=required_cols_quotes,
                        decimal_fields=decimal_cols_quotes,
                        fields_to_remove_before_update=fields_to_remove_quotes
                    ):
                        st.rerun()
        # else: error or no quotes message already handled

    with tab_bidders:
        st.subheader("Gerenciar Licitantes")
        
        df_bidders_raw = load_and_prepare_data(bidder_repo, "Licitantes")

        if df_bidders_raw is not None and not df_bidders_raw.empty:
            cols_to_display_bidders = ["id", "name", "website", "email", "phone", "desc", "created_at", "updated_at"]
            # Ensure all display columns exist
            for col in cols_to_display_bidders:
                if col not in df_bidders_raw.columns:
                    df_bidders_raw[col] = None
            
            df_display_bidders_unfiltered = df_bidders_raw[cols_to_display_bidders].copy()

            search_columns_bidders = ["name", "website", "email", "phone", "desc"]
            df_filtered_bidders = display_search_box_and_filter_df(
                df_unfiltered=df_display_bidders_unfiltered,
                search_columns=search_columns_bidders,
                search_key_suffix="bidders_tab",
                entity_name_plural="Licitantes",
                search_label="Buscar Licitantes (por nome, website, email, etc.):"
            )

            column_config_bidders = {
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Nome", required=True),
                "website": st.column_config.TextColumn("Website"),
                "email": st.column_config.TextColumn("Email"),
                "phone": st.column_config.TextColumn("Telefone"),
                "desc": st.column_config.TextColumn("Descrição/Observações"), # Model field is 'desc'
                "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
            }
            
            original_df_for_save_bidders = df_filtered_bidders.copy()

            edited_bidders_df = display_data_editor(
                df_to_edit=df_filtered_bidders,
                column_config=column_config_bidders,
                editor_key_suffix="bidders_tab" # Original key was "editor_licitantes_tab"
            )

            if st.button("Salvar Alterações em Licitantes", key="save_bidders_tab"): # Original key was "save_licitantes_tab"
                editable_cols_bidders = ["name", "website", "email", "phone", "desc"]
                required_cols_bidders = ["name"]
                
                if handle_save_changes(
                    original_df=original_df_for_save_bidders,
                    edited_df=edited_bidders_df,
                    repository=bidder_repo,
                    entity_name_singular="Licitante",
                    editable_columns=editable_cols_bidders,
                    required_fields=required_cols_bidders
                ):
                    st.rerun()
        # else: load_and_prepare_data already showed messages for None or empty

    with tab_bids:
        st.subheader("Gerenciar Lances")

        # Step 1: Load raw data lists
        bids_list_raw = None
        items_list_for_bids_map = {}
        bidders_list_for_bids_map = {}
        error_loading_bids_data = False
        NO_BIDDER_DISPLAY_NAME = "Nenhum Licitante"

        try:
            bids_list_raw = bid_repo.get_all()
            items_list = item_repo.get_all()
            bidders_list = bidder_repo.get_all()

            if items_list:
                items_list_for_bids_map = {item.id: item.name for item in items_list}
            if bidders_list:
                bidders_list_for_bids_map = {bidder.id: bidder.name for bidder in bidders_list}
        except Exception as e:
            st.error(f"Erro ao carregar dados brutos para Lances: {e}")
            error_loading_bids_data = True

        if not error_loading_bids_data:
            if not bids_list_raw:
                st.info("Nenhum lance cadastrado.")
            else:
                # Step 2: Build Initial DataFrame for display
                bids_data_for_display = []
                for bid in bids_list_raw:
                    bids_data_for_display.append({
                        "id": bid.id,
                        "item_name": items_list_for_bids_map.get(bid.item_id, "Item Desconhecido"),
                        "bidder_name": bidders_list_for_bids_map.get(bid.bidder_id, NO_BIDDER_DISPLAY_NAME) if bid.bidder_id else NO_BIDDER_DISPLAY_NAME,
                        "price": bid.price,
                        "notes": bid.notes,
                        "item_id": bid.item_id,
                        "bidding_id": bid.bidding_id,
                        "bidder_id": bid.bidder_id,
                        "created_at": bid.created_at,
                        "updated_at": bid.updated_at,
                    })
                
                df_bids_built = pd.DataFrame(bids_data_for_display)
                if "created_at" in df_bids_built.columns:
                    df_bids_built["created_at"] = pd.to_datetime(df_bids_built["created_at"], errors='coerce')
                if "updated_at" in df_bids_built.columns:
                    df_bids_built["updated_at"] = pd.to_datetime(df_bids_built["updated_at"], errors='coerce')

                # Step 3: Define display columns
                cols_to_display_bids = [
                    "id", "item_name", "bidder_name", "price", "notes", "item_id", 
                    "bidding_id", "bidder_id", "created_at", "updated_at"
                ]
                for col in cols_to_display_bids:
                    if col not in df_bids_built.columns:
                        df_bids_built[col] = None
                df_display_bids_unfiltered = df_bids_built[cols_to_display_bids].copy()

                # Step 4: Search
                search_columns_bids = ["item_name", "bidder_name", "notes"]
                df_filtered_bids = display_search_box_and_filter_df(
                    df_unfiltered=df_display_bids_unfiltered,
                    search_columns=search_columns_bids,
                    search_key_suffix="bids_tab",
                    entity_name_plural="Lances",
                    search_label="Buscar Lances (por item, licitante, notas):"
                )

                # Step 5: Data Editor
                column_config_bids = {
                    "id": st.column_config.NumberColumn("ID Lance", disabled=True),
                    "item_name": st.column_config.TextColumn("Item", disabled=True),
                    "bidder_name": st.column_config.TextColumn("Licitante", disabled=True),
                    "price": st.column_config.NumberColumn("Preço Ofertado", format="R$ %.2f", min_value=0.01, required=True, help="Valor do lance."),
                    "notes": st.column_config.TextColumn("Notas do Lance"),
                    "item_id": st.column_config.NumberColumn("ID Item (Ref)", disabled=True),
                    "bidding_id": st.column_config.NumberColumn("ID Licitação (Ref)", disabled=True),
                    "bidder_id": st.column_config.NumberColumn("ID Licitante (Ref)", disabled=True),
                    "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
                    "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
                }
                
                original_df_for_save_bids = df_filtered_bids.copy()

                edited_bids_df = display_data_editor(
                    df_to_edit=df_filtered_bids,
                    column_config=column_config_bids,
                    editor_key_suffix="bids_tab"
                )

                # Step 6: Save Changes
                if st.button("Salvar Alterações em Lances", key="save_bids_tab"):
                    editable_cols_bids = ["price", "notes"]
                    required_cols_bids = ["price"] 
                    decimal_cols_bids = ["price"]
                    
                    # item_id, bidding_id, bidder_id are not editable in this view
                    fields_to_remove_bids = ['item_name', 'bidder_name', 'item_id', 'bidding_id', 'bidder_id']

                    if handle_save_changes(
                        original_df=original_df_for_save_bids,
                        edited_df=edited_bids_df,
                        repository=bid_repo,
                        entity_name_singular="Lance",
                        editable_columns=editable_cols_bids,
                        required_fields=required_cols_bids,
                        decimal_fields=decimal_cols_bids,
                        fields_to_remove_before_update=fields_to_remove_bids
                    ):
                        st.rerun()
        # else: error or no bids message already handled
