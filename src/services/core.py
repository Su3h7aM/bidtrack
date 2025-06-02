from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid
from repository import SQLModelRepository


# Bidding Management Functions
def delete_bidding(bidding_repo: SQLModelRepository[Bidding], item_repo: SQLModelRepository[Item],
                   quote_repo: SQLModelRepository[Quote], bid_repo: SQLModelRepository[Bid],
                   bidding_id: int) -> bool:
    # Inline the logic from get_items_by_bidding_id
    all_items = item_repo.get_all()
    items_to_delete = [item for item in all_items if item.bidding_id == bidding_id]

    for item_model in items_to_delete: # Renamed 'item' to 'item_model' to avoid conflict with Item model import
        if item_model.id is not None:
            # Call delete_item, which itself will handle related quotes and bids for that item
            delete_item(item_repo, quote_repo, bid_repo, item_model.id)
            # Ensure the item itself is deleted if delete_item doesn't (though it should)
            # item_repo.delete(item_model.id) # This line is redundant if delete_item works as expected

    return bidding_repo.delete(bidding_id)


# Item Management Functions
def delete_item(item_repo: SQLModelRepository[Item], quote_repo: SQLModelRepository[Quote],
                bid_repo: SQLModelRepository[Bid], item_id: int) -> bool:
    # Inline the logic from get_quotes_by_item_id
    all_quotes = quote_repo.get_all()
    quotes_to_delete = [quote for quote in all_quotes if quote.item_id == item_id]
    for quote in quotes_to_delete:
        if quote.id is not None:
            quote_repo.delete(quote.id)

    # Inline the logic from get_bids_by_item_id
    all_bids = bid_repo.get_all()
    bids_to_delete = [bid for bid in all_bids if bid.item_id == item_id]
    for bid in bids_to_delete:
        if bid.id is not None:
            bid_repo.delete(bid.id)

    return item_repo.delete(item_id)


# Supplier Management Functions
def delete_supplier(supplier_repo: SQLModelRepository[Supplier], quote_repo: SQLModelRepository[Quote],
                    supplier_id: int) -> bool:
    # Inline the logic for finding related quotes
    all_quotes = quote_repo.get_all()
    quotes_to_delete = [quote for quote in all_quotes if quote.supplier_id == supplier_id]
    for quote in quotes_to_delete:
        if quote.id is not None:
            quote_repo.delete(quote.id)

    return supplier_repo.delete(supplier_id)


# Competitor Management Functions
def delete_competitor(competitor_repo: SQLModelRepository[Competitor], bid_repo: SQLModelRepository[Bid],
                      competitor_id: int) -> bool:
    # Inline the logic for finding related bids
    all_bids = bid_repo.get_all()
    bids_to_delete = [bid for bid in all_bids if bid.competitor_id == competitor_id]
    for bid in bids_to_delete:
        if bid.id is not None:
            bid_repo.delete(bid.id)

    return competitor_repo.delete(competitor_id)

# Quote and Bid management functions (add_quote, add_bid, get_quotes_by_item_id, get_bids_by_item_id)
# are removed as they are simple pass-throughs.
# Other get_all, get_by_id, and save functions are also removed.

# Final check on imports:
# Any is no longer needed.
# Bidding, Item, Supplier, Competitor, Quote, Bid are used as type hints in the remaining functions.
# SQLModelRepository is used as a type hint.
# So, the import for 'Any' can be removed.
