import streamlit as st
# Import repository types for type hinting if desired - e.g.
# from db.repositories import (
#     BiddingRepository, ItemRepository, SupplierRepository,
#     QuoteRepository, BidderRepository, BidRepository
# )

# Import the new tab-specific display functions
from ..tabs.supplier import display_suppliers_tab
from ..tabs.bidder import display_bidders_tab
from ..tabs.bidding import display_biddings_tab
from ..tabs.item import display_items_tab
from ..tabs.quote import display_quotes_tab
from ..tabs.bid import display_bids_tab


def show_management_tables_view(
    bidding_repo, # : BiddingRepository,
    item_repo,    # : ItemRepository,
    supplier_repo,# : SupplierRepository,
    quote_repo,   # : QuoteRepository,
    bidder_repo,  # : BidderRepository,
    bid_repo      # : BidRepository
):
    """
    Displays the main management tables page with different tabs for each entity.
    Each tab's content is now delegated to a specific display function.
    """
    st.title("Gerenciamento de Tabelas do Sistema")

    tab_labels = ["Licitações", "Itens", "Fornecedores", "Orçamentos", "Licitantes", "Lances"]
    

    tabs = st.tabs(tab_labels)

    # Assign content to each tab by calling the respective display function
    with tabs[0]: # Licitações
        display_biddings_tab(bidding_repo)

    with tabs[1]: # Itens
        # Items tab needs bidding_repo for parent selection
        display_items_tab(item_repo, bidding_repo)

    with tabs[2]: # Fornecedores
        display_suppliers_tab(supplier_repo)

    with tabs[3]: # Orçamentos
        # Quotes tab needs bidding_repo (parent selection), item_repo, supplier_repo (for data prep)
        display_quotes_tab(quote_repo, bidding_repo, item_repo, supplier_repo)

    with tabs[4]: # Licitantes
        display_bidders_tab(bidder_repo)

    with tabs[5]: # Lances
        # Bids tab needs bidding_repo (parent selection), item_repo, bidder_repo (for data prep)
        display_bids_tab(bid_repo, bidding_repo, item_repo, bidder_repo)

# Removed all previous configuration dicts and helper functions as they are now in their respective tab_content files.
# Kept imports for Streamlit and potentially repository types for the main function signature.
# Removed pandas, Decimal, BiddingMode, get_options_map, get_quotes_dataframe as they are now used within
# the specific tab_content files or generic_entity_management.py.
