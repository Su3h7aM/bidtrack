import streamlit as st
import pandas as pd
from decimal import Decimal # Required for quote fields
from db.models import BiddingMode # Required for mode handling
from ..ui.utils import get_options_map # For Licitação selection
from ..services.dataframes import get_quotes_dataframe # To get calculated_price logic easily

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
        try:
            biddings_list = bidding_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar dados de Licitações: {e}")
            return

        if not biddings_list:
            st.info("Nenhuma licitação cadastrada.")
            return 

        # Convert to DataFrame
        df_biddings = pd.DataFrame([b.model_dump() for b in biddings_list])
        
        # Prepare display columns, especially mode and date
        df_biddings["mode_display"] = df_biddings["mode"].apply(lambda x: x.value if isinstance(x, BiddingMode) else x)
        # Ensure 'date' is datetime for column_config
        df_biddings["date"] = pd.to_datetime(df_biddings["date"])
        df_biddings["created_at"] = pd.to_datetime(df_biddings["created_at"])
        df_biddings["updated_at"] = pd.to_datetime(df_biddings["updated_at"])

        cols_to_display = ["id", "process_number", "city", "mode_display", "date", "description", "status", "created_at", "updated_at"]
        # Ensure all columns exist, add if missing (e.g. description, status might be new)
        for col in cols_to_display:
            if col not in df_biddings.columns:
                if col == "mode_display": # if original 'mode' was used to create this
                     df_biddings[col] = df_biddings["mode"].apply(lambda x: x.value if isinstance(x, BiddingMode) else x)
                else:
                    df_biddings[col] = None 
        
        df_display_biddings = df_biddings[cols_to_display].copy()


        search_term = st.text_input("Buscar Licitações (por nº processo, cidade, modo):", key="search_licitacoes")
        
        unfiltered_df_biddings = df_display_biddings # Keep a reference before filtering
        
        if search_term:
            search_term_lower = search_term.lower()
            filtered_df_biddings = unfiltered_df_biddings[ # Filter from the unfiltered copy
                unfiltered_df_biddings["process_number"].astype(str).str.lower().str.contains(search_term_lower) |
                unfiltered_df_biddings["city"].astype(str).str.lower().str.contains(search_term_lower) |
                unfiltered_df_biddings["mode_display"].astype(str).str.lower().str.contains(search_term_lower)
            ]
        else:
            filtered_df_biddings = unfiltered_df_biddings # Show all if no search term

        if filtered_df_biddings.empty and not unfiltered_df_biddings.empty and search_term:
            st.info("Nenhum resultado encontrado para sua busca em Licitações.")
            # Optionally, you might want to return or not display the editor if the search yields nothing
            # For now, we'll let it display an empty editor or handle as data_editor does.

        column_config_biddings = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "process_number": st.column_config.TextColumn("Nº do Processo", required=True),
            "city": st.column_config.TextColumn("Cidade", required=True),
            "mode_display": st.column_config.SelectboxColumn(
                "Modalidade", 
                options=[mode.value for mode in BiddingMode],
                required=True
            ),
            "date": st.column_config.DatetimeColumn("Data", format="YYYY-MM-DD HH:mm", required=True),
            "description": st.column_config.TextColumn("Descrição"),
            "status": st.column_config.TextColumn("Status"), 
            "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
            "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
        }

        edited_df_biddings = st.data_editor(
            filtered_df_biddings, 
            key="editor_licitacoes", 
            column_config=column_config_biddings, 
            num_rows="dynamic", # Keep as dynamic for now, though delete needs separate handling
            use_container_width=True
        )

        if st.button("Salvar Alterações em Licitações", key="save_licitacoes"):
            changes_found = False
            original_df_subset = filtered_df_biddings.set_index('id')
            edited_df_subset = edited_df_biddings.set_index('id')

            for licitacao_id, edited_row in edited_df_subset.iterrows():
                if licitacao_id not in original_df_subset.index: # New row
                    # Logic for adding new rows - not directly supported by comparing original_df_subset
                    # For now, we focus on updates. New row addition would typically be via a separate form/dialog.
                    # st.warning(f"Linha com ID {licitacao_id} parece ser nova. Adição não suportada diretamente aqui.")
                    continue

                original_row = original_df_subset.loc[licitacao_id]
                update_dict = {}
                
                for col_name in edited_df_subset.columns:
                    original_value = original_row[col_name]
                    edited_value = edited_row[col_name]

                    # Handle NaT/None comparison and type differences carefully
                    if pd.isna(original_value) and pd.isna(edited_value):
                        continue
                    if isinstance(original_value, (pd.Timestamp, pd.NaTType)) and isinstance(edited_value, (pd.Timestamp, pd.NaTType)):
                        if (pd.isna(original_value) and pd.isna(edited_value)) or (original_value == edited_value):
                            continue
                    elif str(original_value) == str(edited_value): # General comparison after handling NaT
                         continue

                    update_dict[col_name] = edited_value
                
                if update_dict:
                    changes_found = True
                    try:
                        if "mode_display" in update_dict:
                            try:
                                mode_val = update_dict.pop("mode_display")
                                update_dict["mode"] = BiddingMode(mode_val)
                            except ValueError:
                                st.error(f"Valor inválido para Modalidade ('{mode_val}') na Licitação ID {licitacao_id}. Alterações não salvas para esta linha.")
                                continue # Skip this row
                        
                        if "date" in update_dict and isinstance(update_dict["date"], str):
                            try:
                                update_dict["date"] = pd.to_datetime(update_dict["date"])
                            except ValueError:
                                st.error(f"Data inválida ('{update_dict['date']}') na Licitação ID {licitacao_id}. Alterações não salvas para esta linha.")
                                continue # Skip this row
                        
                        update_dict.pop("id", None) 
                        update_dict.pop("created_at", None)
                        update_dict.pop("updated_at", None)
                        
                        bidding_repo.update(licitacao_id, update_dict)
                        st.success(f"Licitação ID {licitacao_id} atualizada com sucesso.")
                    except Exception as e:
                        st.error(f"Falha ao salvar Licitação ID {licitacao_id}: {e}")
            
            if changes_found:
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar.")

    with tab_items:
        st.subheader("Gerenciar Itens")
        
        # Step 1: Select Bidding
        all_biddings_for_item_tab = None
        try:
            all_biddings_for_item_tab = bidding_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar Licitações para seleção: {e}")
        
        if not all_biddings_for_item_tab:
            st.info("Nenhuma licitação cadastrada para selecionar e listar itens.")
        else:
            bidding_options_map, bidding_option_ids = get_options_map(
                data_list=all_biddings_for_item_tab, 
                extra_cols=["city", "process_number", "mode"], 
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

                if df_all_items_raw is not None: 
                    df_items_for_selected_bidding = df_all_items_raw[
                        df_all_items_raw["bidding_id"] == selected_bidding_id_for_items
                    ].copy() 

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
                            "quantity": st.column_config.NumberColumn("Quantidade", format="%.2f", min_value=0.00, required=True),
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
                            fields_to_remove_items = ["bidding_id"] 

                            if handle_save_changes(
                                original_df=original_df_for_save_items,
                                edited_df=edited_items_df,
                                repository=item_repo,
                                entity_name_singular="Item",
                                editable_columns=editable_cols_items,
                                required_fields=required_cols_items,
                                fields_to_remove_before_update=fields_to_remove_items
                            ):
                                st.rerun()

    with tab_suppliers:
        st.subheader("Gerenciar Fornecedores")
        try:
            suppliers_list = supplier_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar dados de Fornecedores: {e}")
            return

        if not suppliers_list:
            st.info("Nenhum fornecedor cadastrado.")
            return

        df_suppliers = pd.DataFrame([s.model_dump() for s in suppliers_list])
        # Ensure date columns are datetime
        df_suppliers["created_at"] = pd.to_datetime(df_suppliers["created_at"])
        df_suppliers["updated_at"] = pd.to_datetime(df_suppliers["updated_at"])

        cols_to_display_suppliers = ["id", "name", "website", "email", "phone", "desc", "created_at", "updated_at"]
        # Ensure all columns exist
        for col in cols_to_display_suppliers:
            if col not in df_suppliers.columns:
                 df_suppliers[col] = None 
        
        df_display_suppliers = df_suppliers[cols_to_display_suppliers].copy()
        
        search_term_suppliers = st.text_input("Buscar Fornecedores (por nome, website, email, etc.):", key="search_fornecedores_tab")
        
        unfiltered_df_suppliers = df_display_suppliers # Keep ref
        
        if search_term_suppliers:
            search_term_lower_suppliers = search_term_suppliers.lower()
            filtered_df_suppliers = unfiltered_df_suppliers[ # filter from unfiltered
                unfiltered_df_suppliers["name"].astype(str).str.lower().str.contains(search_term_lower_suppliers) |
                unfiltered_df_suppliers["website"].astype(str).str.lower().str.contains(search_term_lower_suppliers) |
                unfiltered_df_suppliers["email"].astype(str).str.lower().str.contains(search_term_lower_suppliers) |
                unfiltered_df_suppliers["phone"].astype(str).str.lower().str.contains(search_term_lower_suppliers) |
                unfiltered_df_suppliers["desc"].astype(str).str.lower().str.contains(search_term_lower_suppliers)
            ]
        else:
            filtered_df_suppliers = unfiltered_df_suppliers
            
        if filtered_df_suppliers.empty and not unfiltered_df_suppliers.empty and search_term_suppliers:
            st.info("Nenhum resultado encontrado para sua busca em Fornecedores.")

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

        edited_suppliers_df = st.data_editor(
            filtered_df_suppliers,
            key="editor_fornecedores_tab",
            column_config=column_config_suppliers,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("Salvar Alterações em Fornecedores", key="save_fornecedores_tab"):
            supplier_changes_found = False
            original_suppliers_subset = filtered_df_suppliers.set_index('id')
            edited_suppliers_subset = edited_suppliers_df.set_index('id')

            for supplier_id, edited_supplier_row in edited_suppliers_subset.iterrows():
                if supplier_id not in original_suppliers_subset.index:
                    continue # Skip new rows for now

                original_supplier_row = original_suppliers_subset.loc[supplier_id]
                supplier_update_dict = {}

                for col_name_supplier in edited_suppliers_subset.columns:
                    original_supplier_value = original_supplier_row[col_name_supplier]
                    edited_supplier_value = edited_supplier_row[col_name_supplier]
                    
                    if pd.isna(original_supplier_value) and pd.isna(edited_supplier_value):
                        continue
                    if isinstance(original_supplier_value, (pd.Timestamp, pd.NaTType)) and isinstance(edited_supplier_value, (pd.Timestamp, pd.NaTType)):
                        if (pd.isna(original_supplier_value) and pd.isna(edited_supplier_value)) or (original_supplier_value == edited_supplier_value):
                            continue
                    elif str(original_supplier_value) == str(edited_supplier_value):
                        continue
                    
                    supplier_update_dict[col_name_supplier] = edited_supplier_value
                
                if supplier_update_dict:
                    supplier_changes_found = True
                    try:
                        # Remove fields that should not be updated
                        supplier_update_dict.pop("id", None)
                        supplier_update_dict.pop("created_at", None)
                        supplier_update_dict.pop("updated_at", None)
                        
                        supplier_repo.update(supplier_id, supplier_update_dict)
                        st.success(f"Fornecedor ID {supplier_id} atualizado com sucesso.")
                    except Exception as e:
                        st.error(f"Falha ao salvar Fornecedor ID {supplier_id}: {e}")
            
            if supplier_changes_found:
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar em Fornecedores.")

    with tab_quotes:
        st.subheader("Gerenciar Orçamentos")

        # Step 1: Add Bidding Selection
        all_biddings_for_quotes_tab = None
        try:
            all_biddings_for_quotes_tab = bidding_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar Licitações para seleção: {e}")
            all_biddings_for_quotes_tab = [] 

        if not all_biddings_for_quotes_tab:
            st.info("Nenhuma licitação cadastrada para selecionar orçamentos.")
        else:
            bidding_options_map_quotes, bidding_option_ids_quotes = get_options_map(
                data_list=all_biddings_for_quotes_tab, 
                extra_cols=["city", "process_number", "mode"], 
                default_message="Selecione uma Licitação para ver os orçamentos...",
            )
            selected_bidding_id_for_quotes = st.selectbox(
                "Escolha uma Licitação para ver os orçamentos:",
                options=bidding_option_ids_quotes,
                format_func=lambda x: bidding_options_map_quotes.get(x, "Selecione..."),
                key="select_bidding_for_quotes_tab",
            )

            if selected_bidding_id_for_quotes is None:
                st.info("Por favor, selecione uma licitação.")
            else:
                # Step 2: Fetch Items for Selected Bidding
                all_items_list = None
                try:
                    all_items_list = item_repo.get_all()
                except Exception as e:
                    st.error(f"Erro ao carregar itens para a licitação selecionada: {e}")
                
                if all_items_list is None:
                    st.info("Não foi possível carregar os itens.") 
                else:
                    items_for_selected_bidding = [
                        item for item in all_items_list if item.bidding_id == selected_bidding_id_for_quotes
                    ]
                    if not items_for_selected_bidding:
                        st.info("Nenhum item encontrado para esta licitação. Não é possível listar orçamentos.")
                    else:
                        item_ids_for_selected_bidding = {item.id for item in items_for_selected_bidding}

                        # Step 3: Filter Quotes Based on Items of Selected Bidding
                        all_quotes_list_raw = None
                        try:
                            all_quotes_list_raw = quote_repo.get_all()
                            # Need all suppliers for mapping later, even if some quotes are filtered out
                            suppliers_list_quotes_tab = supplier_repo.get_all() 
                            items_list_quotes_tab = all_items_list # Use already fetched items
                        except Exception as e:
                            st.error(f"Erro ao carregar orçamentos ou dados de suporte: {e}")
                            all_quotes_list_raw = None # Ensure it's None to prevent further processing

                        if all_quotes_list_raw is None:
                            st.info("Não foi possível carregar os orçamentos.")
                        else:
                            quotes_list = [ # Renaming to quotes_list to match original variable name
                                quote for quote in all_quotes_list_raw if quote.item_id in item_ids_for_selected_bidding
                            ]

                            if not quotes_list: # Check the filtered list
                                st.info("Nenhum orçamento cadastrado para os itens desta licitação.")
                                # Let it proceed to show empty editor if needed by not returning
                            
                            # Original logic for building quotes_data_for_editor starts here, using the filtered 'quotes_list'
                            items_map = {item.id: item.name for item in items_list_quotes_tab} if items_list_quotes_tab else {}
                            suppliers_map = {sup.id: sup.name for sup in suppliers_list_quotes_tab} if suppliers_list_quotes_tab else {}

                            quotes_data_for_editor = []
                            for quote in quotes_list: # Iterate over filtered list
                                supplier_name = suppliers_map.get(quote.supplier_id, "N/A")
                                item_name = items_map.get(quote.item_id, "N/A")
            
            # Calculate price for display
            base_price = quote.price if quote.price else Decimal(0)
            freight = quote.freight if quote.freight else Decimal(0)
            additional_costs = quote.additional_costs if quote.additional_costs else Decimal(0)
            taxes_percentage = quote.taxes if quote.taxes else Decimal(0)
            margin_percentage = quote.margin if quote.margin else Decimal(0)
            
            price_with_freight_costs = base_price + freight + additional_costs
            taxes_value = price_with_freight_costs * (taxes_percentage / Decimal(100))
            price_before_margin = price_with_freight_costs + taxes_value
            margin_value = price_before_margin * (margin_percentage / Decimal(100))
            calculated_price = price_before_margin + margin_value

            quotes_data_for_editor.append({
                "id": quote.id,
                "item_name": item_name,
                "supplier_name": supplier_name,
                "price": quote.price, # base cost
                "freight": quote.freight,
                "additional_costs": quote.additional_costs,
                "taxes": quote.taxes, # percentage
                "margin": quote.margin, # percentage
                "calculated_price": calculated_price, # For display
                "notes": quote.notes,
                "item_id": quote.item_id, # Keep for reference if needed, but disable
                "supplier_id": quote.supplier_id, # Keep for reference if needed, but disable
                "created_at": quote.created_at,
                "updated_at": quote.updated_at,
            })
        
        df_quotes = pd.DataFrame(quotes_data_for_editor)
        df_quotes["created_at"] = pd.to_datetime(df_quotes["created_at"])
        df_quotes["updated_at"] = pd.to_datetime(df_quotes["updated_at"])

        search_term_quotes = st.text_input("Buscar Orçamentos (por item, fornecedor, notas):", key="search_orcamentos_tab")
        
        unfiltered_df_quotes = df_quotes # Keep ref
        
        if search_term_quotes:
            search_term_lower_quotes = search_term_quotes.lower()
            filtered_df_quotes = unfiltered_df_quotes[ # filter from unfiltered
                unfiltered_df_quotes["item_name"].astype(str).str.lower().str.contains(search_term_lower_quotes) |
                unfiltered_df_quotes["supplier_name"].astype(str).str.lower().str.contains(search_term_lower_quotes) |
                unfiltered_df_quotes["notes"].astype(str).str.lower().str.contains(search_term_lower_quotes)
            ]
        else:
            filtered_df_quotes = unfiltered_df_quotes

        if filtered_df_quotes.empty and not unfiltered_df_quotes.empty and search_term_quotes:
            st.info("Nenhum resultado encontrado para sua busca em Orçamentos.")

        column_config_quotes = {
            "id": st.column_config.NumberColumn("ID Orçamento", disabled=True), # Changed label
            "item_name": st.column_config.TextColumn("Nome do Item", disabled=True), # Changed label
            "supplier_name": st.column_config.TextColumn("Nome do Fornecedor", disabled=True), # Changed label
            "price": st.column_config.NumberColumn("Preço Base (Custo)", format="R$ %.2f", min_value=0.01, required=True, help="Custo base do produto/serviço."), # Added min_value
            "freight": st.column_config.NumberColumn("Frete (R$)", format="R$ %.2f", min_value=0.00, required=False),
            "additional_costs": st.column_config.NumberColumn("Custos Adicionais (R$)", format="R$ %.2f", min_value=0.00, required=False),
            "taxes": st.column_config.NumberColumn("Impostos (%)", format="%.2f", min_value=0.00, help="Ex: 6 para 6%", required=False),
            "margin": st.column_config.NumberColumn("Margem (%)", format="%.2f", min_value=0.00, help="Ex: 20 para 20%", required=True),
            "calculated_price": st.column_config.NumberColumn("Preço Calculado", format="R$ %.2f", disabled=True, help="Preço final após custos, impostos e margem."),
            "notes": st.column_config.TextColumn("Notas do Orçamento"), # Changed label
            "item_id": st.column_config.NumberColumn("ID do Item (Ref)", disabled=True), # Changed label
            "supplier_id": st.column_config.NumberColumn("ID do Fornecedor (Ref)", disabled=True), # Changed label
            "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
            "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
        }

        # Select and order columns for display
        cols_for_editor = ["id", "item_name", "supplier_name", "price", "freight", "additional_costs", "taxes", "margin", "calculated_price", "notes", "item_id", "supplier_id", "created_at", "updated_at"]
        display_df_quotes = filtered_df_quotes[cols_for_editor]


        edited_quotes_df = st.data_editor(
            display_df_quotes,
            key="editor_orcamentos_tab",
            column_config=column_config_quotes,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("Salvar Alterações em Orçamentos", key="save_orcamentos_tab"):
            quote_changes_found = False
            # Use display_df_quotes for original comparison structure if it matches edited_quotes_df structure
            original_quotes_subset = display_df_quotes.set_index('id') 
            edited_quotes_subset = edited_quotes_df.set_index('id')

            for quote_id, edited_quote_row in edited_quotes_subset.iterrows():
                if quote_id not in original_quotes_subset.index:
                    continue 

                original_quote_row = original_quotes_subset.loc[quote_id]
                quote_update_dict = {}

                editable_fields = ["price", "freight", "additional_costs", "taxes", "margin", "notes"]
                for col_name_quote in editable_fields:
                    original_quote_value = original_quote_row[col_name_quote]
                    edited_quote_value = edited_quote_row[col_name_quote]
                    
                    # Handle NaN/None for numeric/Decimal, and string comparison
                    if pd.isna(original_quote_value) and pd.isna(edited_quote_value):
                        continue
                    # Convert to string for comparison to handle type differences like Decimal vs float from editor
                    if str(original_quote_value) == str(edited_quote_value):
                        continue
                    
                    # If edited value is empty string for a numeric field, treat as None or skip
                    if edited_quote_value == "" and col_name_quote in ["freight", "additional_costs", "taxes", "notes"]:
                         quote_update_dict[col_name_quote] = None
                    elif col_name_quote in ["price", "margin"] and edited_quote_value == "": # Required fields
                        st.error(f"Campo '{col_name_quote}' é obrigatório para o orçamento ID {quote_id}.")
                        continue # Skip this update
                    else:
                        quote_update_dict[col_name_quote] = edited_quote_value
                
                if quote_update_dict:
                    quote_changes_found = True
                    try:
                        for key_decimal in ['price', 'freight', 'additional_costs', 'taxes', 'margin']:
                            if key_decimal in quote_update_dict and quote_update_dict[key_decimal] is not None:
                                try:
                                    quote_update_dict[key_decimal] = Decimal(str(quote_update_dict[key_decimal]))
                                except ValueError:
                                    st.error(f"Valor inválido para '{key_decimal}' ('{quote_update_dict[key_decimal]}') no Orçamento ID {quote_id}.")
                                    # Remove problematic key or skip update for this row
                                    quote_update_dict.pop(key_decimal) 
                                    # Potentially skip this entire row's update if a required decimal field is invalid
                                    if key_decimal in ["price", "margin"]: 
                                        st.warning(f"Orçamento ID {quote_id} não atualizado devido a valor inválido em campo obrigatório.")
                                        # To skip, we need a flag or to put the repo.update in an else block
                                        # For now, let's assume it might proceed with partial data if not required, or fail at repo
                                        continue # Or set a flag to skip repo.update for this row
                            elif key_decimal in quote_update_dict and quote_update_dict[key_decimal] is None and key_decimal not in ["notes", "freight", "additional_costs", "taxes"]:
                                # If a required field (price, margin) becomes None after edit (e.g. editor bug or cleared non-string), error
                                st.error(f"Campo '{key_decimal}' é obrigatório e não pode ser vazio no Orçamento ID {quote_id}.")
                                # This state should ideally be prevented by required=True in data_editor,
                                # but as a safeguard.
                                continue # Skip update for this row
                            elif key_decimal in ["freight", "additional_costs", "taxes"] and quote_update_dict.get(key_decimal) is None:
                                quote_update_dict[key_decimal] = Decimal("0.00") # Default optional Decimals to 0.00 if None

                        if not quote_update_dict: # If all changes were problematic or no actual changes
                            st.info(f"Nenhuma alteração válida para salvar para o Orçamento ID {quote_id}.")
                            continue

                        quote_repo.update(quote_id, quote_update_dict)
                        st.success(f"Orçamento ID {quote_id} atualizado com sucesso.")
                    except Exception as e:
                        st.error(f"Falha ao salvar Orçamento ID {quote_id}: {e}")
            
            if quote_changes_found:
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar em Orçamentos.")

    with tab_bidders:
        st.subheader("Gerenciar Licitantes") 
        try:
            bidders_list = bidder_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar dados de Licitantes: {e}")
            return

        if not bidders_list:
            st.info("Nenhum licitante cadastrado.")
            return

        df_bidders = pd.DataFrame([b.model_dump() for b in bidders_list])
        # Ensure date columns are datetime
        df_bidders["created_at"] = pd.to_datetime(df_bidders["created_at"])
        df_bidders["updated_at"] = pd.to_datetime(df_bidders["updated_at"])

        cols_to_display_bidders = ["id", "name", "website", "email", "phone", "desc", "created_at", "updated_at"]
        # Ensure all columns exist
        for col in cols_to_display_bidders:
            if col not in df_bidders.columns:
                 df_bidders[col] = None 
        
        df_display_bidders = df_bidders[cols_to_display_bidders].copy()
        
        search_term_bidders = st.text_input("Buscar Licitantes (por nome, website, email, etc.):", key="search_licitantes_tab")
        
        unfiltered_df_bidders = df_display_bidders # Keep ref
        
        if search_term_bidders:
            search_term_lower_bidders = search_term_bidders.lower()
            filtered_df_bidders = unfiltered_df_bidders[ # filter from unfiltered
                unfiltered_df_bidders["name"].astype(str).str.lower().str.contains(search_term_lower_bidders) |
                unfiltered_df_bidders["website"].astype(str).str.lower().str.contains(search_term_lower_bidders) |
                unfiltered_df_bidders["email"].astype(str).str.lower().str.contains(search_term_lower_bidders) |
                unfiltered_df_bidders["phone"].astype(str).str.lower().str.contains(search_term_lower_bidders) |
                unfiltered_df_bidders["desc"].astype(str).str.lower().str.contains(search_term_lower_bidders)
            ]
        else:
            filtered_df_bidders = unfiltered_df_bidders
            
        if filtered_df_bidders.empty and not unfiltered_df_bidders.empty and search_term_bidders:
            st.info("Nenhum resultado encontrado para sua busca em Licitantes.")

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

        edited_bidders_df = st.data_editor(
            filtered_df_bidders,
            key="editor_licitantes_tab",
            column_config=column_config_bidders,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("Salvar Alterações em Licitantes", key="save_licitantes_tab"):
            bidder_changes_found = False
            original_bidders_subset = filtered_df_bidders.set_index('id')
            edited_bidders_subset = edited_bidders_df.set_index('id')

            for bidder_id, edited_bidder_row in edited_bidders_subset.iterrows():
                if bidder_id not in original_bidders_subset.index:
                    continue # Skip new rows for now

                original_bidder_row = original_bidders_subset.loc[bidder_id]
                bidder_update_dict = {}

                for col_name_bidder in edited_bidders_subset.columns:
                    original_bidder_value = original_bidder_row[col_name_bidder]
                    edited_bidder_value = edited_bidder_row[col_name_bidder]
                    
                    if pd.isna(original_bidder_value) and pd.isna(edited_bidder_value):
                        continue
                    if isinstance(original_bidder_value, (pd.Timestamp, pd.NaTType)) and isinstance(edited_bidder_value, (pd.Timestamp, pd.NaTType)):
                        if (pd.isna(original_bidder_value) and pd.isna(edited_bidder_value)) or (original_bidder_value == edited_bidder_value):
                            continue
                    elif str(original_bidder_value) == str(edited_bidder_value):
                        continue
                    
                    bidder_update_dict[col_name_bidder] = edited_bidder_value
                
                if bidder_update_dict:
                    bidder_changes_found = True
                    try:
                        # Remove fields that should not be updated
                        bidder_update_dict.pop("id", None)
                        bidder_update_dict.pop("created_at", None)
                        bidder_update_dict.pop("updated_at", None)
                        
                        bidder_repo.update(bidder_id, bidder_update_dict)
                        st.success(f"Licitante ID {bidder_id} atualizado com sucesso.")
                    except Exception as e:
                        st.error(f"Falha ao salvar Licitante ID {bidder_id}: {e}")
            
            if bidder_changes_found:
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar em Licitantes.")

    with tab_bids:
        st.subheader("Gerenciar Lances")

        # Step 1: Add Bidding Selection
        all_biddings_for_bids_tab = None
        try:
            all_biddings_for_bids_tab = bidding_repo.get_all()
        except Exception as e:
            st.error(f"Erro ao carregar Licitações para seleção: {e}")
            all_biddings_for_bids_tab = [] 

        if not all_biddings_for_bids_tab:
            st.info("Nenhuma licitação cadastrada para selecionar lances.")
        else:
            bidding_options_map_bids, bidding_option_ids_bids = get_options_map(
                data_list=all_biddings_for_bids_tab,
                extra_cols=["city", "process_number", "mode"],
                default_message="Selecione uma Licitação para ver os lances...",
            )
            selected_bidding_id_for_bids = st.selectbox(
                "Escolha uma Licitação para ver os lances:",
                options=bidding_option_ids_bids,
                format_func=lambda x: bidding_options_map_bids.get(x, "Selecione..."),
                key="select_bidding_for_bids_tab",
            )

            if selected_bidding_id_for_bids is None:
                st.info("Por favor, selecione uma licitação.")
            else:
                # Step 2: Filter Bids Based on Selected Bidding
                all_bids_list_raw = None
                items_list_bids_tab = None # For mapping
                bidders_list_bids_tab = None # For mapping
                try:
                    all_bids_list_raw = bid_repo.get_all()
                    items_list_bids_tab = item_repo.get_all() 
                    bidders_list_bids_tab = bidder_repo.get_all()
                except Exception as e:
                    st.error(f"Erro ao carregar lances ou dados de suporte: {e}")
                
                if all_bids_list_raw is None:
                    st.info("Não foi possível carregar os lances.")
                else:
                    bids_list = [ # Renaming to bids_list to match original variable
                        bid for bid in all_bids_list_raw if bid.bidding_id == selected_bidding_id_for_bids
                    ]

                    if not bids_list:
                        st.info("Nenhum lance cadastrado para esta licitação.")
                        # Let it proceed to show empty editor if needed

                    # Mappings (original logic)
                    item_names_map = {item.id: item.name for item in items_list_bids_tab} if items_list_bids_tab else {}
                    bidder_names_map = {bidder.id: bidder.name for bidder in bidders_list_bids_tab} if bidders_list_bids_tab else {}
                    NO_BIDDER_DISPLAY_NAME = "Nenhum Licitante"

                    bids_data_for_editor = []
                    for bid in bids_list: # Iterate over filtered list
                        bids_data_for_editor.append({
                            "id": bid.id,
                            "item_name": item_names_map.get(bid.item_id, "Item Desconhecido"),
                "bidder_name": bidder_names_map.get(bid.bidder_id, NO_BIDDER_DISPLAY_NAME) if bid.bidder_id else NO_BIDDER_DISPLAY_NAME,
                "price": bid.price,
                "notes": bid.notes,
                "item_id": bid.item_id, # For reference
                "bidding_id": bid.bidding_id, # For reference
                "bidder_id": bid.bidder_id, # For reference
                "created_at": bid.created_at,
                "updated_at": bid.updated_at,
            })
        
        df_bids = pd.DataFrame(bids_data_for_editor)
        df_bids["created_at"] = pd.to_datetime(df_bids["created_at"])
        df_bids["updated_at"] = pd.to_datetime(df_bids["updated_at"])

        search_term_bids = st.text_input("Buscar Lances (por item, licitante, notas):", key="search_lances_tab")
        
        unfiltered_df_bids = df_bids # Keep ref
        
        if search_term_bids:
            search_term_lower_bids = search_term_bids.lower()
            filtered_df_bids = unfiltered_df_bids[ # filter from unfiltered
                unfiltered_df_bids["item_name"].astype(str).str.lower().str.contains(search_term_lower_bids) |
                unfiltered_df_bids["bidder_name"].astype(str).str.lower().str.contains(search_term_lower_bids) |
                unfiltered_df_bids["notes"].astype(str).str.lower().str.contains(search_term_lower_bids)
            ]
        else:
            filtered_df_bids = unfiltered_df_bids

        if filtered_df_bids.empty and not unfiltered_df_bids.empty and search_term_bids:
            st.info("Nenhum resultado encontrado para sua busca em Lances.")
            
        column_config_bids = {
            "id": st.column_config.NumberColumn("ID Lance", disabled=True), # Changed label
            "item_name": st.column_config.TextColumn("Nome do Item", disabled=True), # Changed label
            "bidder_name": st.column_config.TextColumn("Nome do Licitante", disabled=True), # Changed label
            "price": st.column_config.NumberColumn("Preço Ofertado", format="R$ %.2f", min_value=0.01, required=True, help="Valor do lance."), # Added min_value
            "notes": st.column_config.TextColumn("Notas do Lance"), # Changed label
            "item_id": st.column_config.NumberColumn("ID do Item (Ref)", disabled=True), # Changed label
            "bidding_id": st.column_config.NumberColumn("ID da Licitação (Ref)", disabled=True), # Changed label
            "bidder_id": st.column_config.NumberColumn("ID do Licitante (Ref)", disabled=True), # Changed label
            "created_at": st.column_config.DatetimeColumn("Criado em", format="YYYY-MM-DD HH:mm", disabled=True),
            "updated_at": st.column_config.DatetimeColumn("Atualizado em", format="YYYY-MM-DD HH:mm", disabled=True),
        }
        
        # Define which columns to display in the editor
        cols_for_bids_editor = ["id", "item_name", "bidder_name", "price", "notes", "item_id", "bidding_id", "bidder_id", "created_at", "updated_at"]
        display_df_bids = filtered_df_bids[cols_for_bids_editor]

        edited_bids_df = st.data_editor(
            display_df_bids,
            key="editor_lances_tab",
            column_config=column_config_bids,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("Salvar Alterações em Lances", key="save_lances_tab"):
            bid_changes_found = False
            original_bids_subset = display_df_bids.set_index('id')
            edited_bids_subset = edited_bids_df.set_index('id')

            for bid_id, edited_bid_row in edited_bids_subset.iterrows():
                if bid_id not in original_bids_subset.index:
                    continue # Skip new rows

                original_bid_row = original_bids_subset.loc[bid_id]
                bid_update_dict = {}

                editable_bid_fields = ["price", "notes"]
                for col_name_bid in editable_bid_fields:
                    original_bid_value = original_bid_row[col_name_bid]
                    edited_bid_value = edited_bid_row[col_name_bid]

                    if pd.isna(original_bid_value) and pd.isna(edited_bid_value):
                        continue
                    if str(original_bid_value) == str(edited_bid_value): # Handles Decimal vs float from editor if stringified
                        continue
                    
                    if col_name_bid == "price" and (edited_bid_value is None or str(edited_bid_value).strip() == ""):
                        st.error(f"Campo 'Preço Ofertado' é obrigatório para o lance ID {bid_id}.")
                        continue # Skip this update
                    
                    bid_update_dict[col_name_bid] = edited_bid_value
                
                if bid_update_dict:
                    bid_changes_found = True
                    try:
                        if 'price' in bid_update_dict:
                            try:
                                price_val = bid_update_dict['price']
                                bid_update_dict['price'] = Decimal(str(price_val))
                                if bid_update_dict['price'] <= Decimal(0):
                                    st.error(f"Preço deve ser positivo para o Lance ID {bid_id}.")
                                    continue
                            except ValueError:
                                st.error(f"Valor inválido para Preço ('{price_val}') no Lance ID {bid_id}.")
                                continue
                        
                        if 'notes' in bid_update_dict and (bid_update_dict['notes'] is None or str(bid_update_dict['notes']).strip() == ""):
                            bid_update_dict['notes'] = None
                            
                        bid_repo.update(bid_id, bid_update_dict)
                        st.success(f"Lance ID {bid_id} atualizado com sucesso.")
                    except Exception as e:
                        st.error(f"Falha ao salvar Lance ID {bid_id}: {e}")
            
            if bid_changes_found:
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada para salvar em Lances.")
