from typing import Any # Required for dict[str, Any] in update methods

from db.models import Bidding, Item, Supplier, Competitor, Quote, Bid
from repository import SQLModelRepository


# Bidding Management Functions
def get_all_biddings(repo: SQLModelRepository[Bidding]) -> list[Bidding]:
    return repo.get_all()


def get_bidding_by_id(repo: SQLModelRepository[Bidding], bidding_id: int) -> Bidding | None:
    return repo.get(bidding_id)


def save_bidding(repo: SQLModelRepository[Bidding], bidding_data: Bidding) -> Bidding:
    if bidding_data.id is None:
        return repo.add(bidding_data)
    else:
        update_data = bidding_data.model_dump(exclude_unset=True, exclude={'id', 'created_at', 'updated_at'})
        updated_bidding = repo.update(bidding_data.id, update_data)
        if updated_bidding is None:
            # This case should ideally not happen if ID exists, but handle defensively
            raise ValueError(f"Bidding with id {bidding_data.id} not found for update.")
        return updated_bidding


def delete_bidding(bidding_repo: SQLModelRepository[Bidding], item_repo: SQLModelRepository[Item],
                   quote_repo: SQLModelRepository[Quote], bid_repo: SQLModelRepository[Bid],
                   bidding_id: int) -> bool:
    items_to_delete = get_items_by_bidding_id(item_repo, bidding_id)
    for item in items_to_delete:
        if item.id is not None: # Should always have an ID if fetched
            # delete_item will handle deleting the item and its related quotes/bids
            delete_item(item_repo, quote_repo, bid_repo, item.id)

    # After all related entities (items and their quotes/bids) are deleted, delete the bidding itself.
    return bidding_repo.delete(bidding_id)


# Item Management Functions
def get_items_by_bidding_id(repo: SQLModelRepository[Item], bidding_id: int) -> list[Item]:
    # TODO: Consider adding a filter method to SQLModelRepository for efficiency
    all_items = repo.get_all()
    return [item for item in all_items if item.bidding_id == bidding_id]


def get_all_items(repo: SQLModelRepository[Item]) -> list[Item]:
    return repo.get_all()


def get_item_by_id(repo: SQLModelRepository[Item], item_id: int) -> Item | None:
    return repo.get(item_id)


def save_item(repo: SQLModelRepository[Item], item_data: Item) -> Item:
    if item_data.id is None:
        return repo.add(item_data)
    else:
        update_data = item_data.model_dump(exclude_unset=True, exclude={'id', 'created_at', 'updated_at'})
        updated_item = repo.update(item_data.id, update_data)
        if updated_item is None:
            raise ValueError(f"Item with id {item_data.id} not found for update.")
        return updated_item


def delete_item(item_repo: SQLModelRepository[Item], quote_repo: SQLModelRepository[Quote],
                bid_repo: SQLModelRepository[Bid], item_id: int) -> bool:
    quotes_to_delete = get_quotes_by_item_id(quote_repo, item_id)
    for quote in quotes_to_delete:
        if quote.id is not None:
            quote_repo.delete(quote.id)

    bids_to_delete = get_bids_by_item_id(bid_repo, item_id)
    for bid in bids_to_delete:
        if bid.id is not None:
            bid_repo.delete(bid.id)

    return item_repo.delete(item_id)


# Supplier Management Functions
def get_all_suppliers(repo: SQLModelRepository[Supplier]) -> list[Supplier]:
    return repo.get_all()


def get_supplier_by_id(repo: SQLModelRepository[Supplier], supplier_id: int) -> Supplier | None:
    return repo.get(supplier_id)


def save_supplier(repo: SQLModelRepository[Supplier], supplier_data: Supplier) -> Supplier:
    if supplier_data.id is None:
        return repo.add(supplier_data)
    else:
        update_data = supplier_data.model_dump(exclude_unset=True, exclude={'id', 'created_at', 'updated_at'})
        updated_supplier = repo.update(supplier_data.id, update_data)
        if updated_supplier is None:
            raise ValueError(f"Supplier with id {supplier_data.id} not found for update.")
        return updated_supplier


def delete_supplier(supplier_repo: SQLModelRepository[Supplier], quote_repo: SQLModelRepository[Quote],
                    supplier_id: int) -> bool:
    # TODO: Consider adding a filter method to SQLModelRepository for efficiency
    all_quotes = quote_repo.get_all()
    quotes_to_delete = [quote for quote in all_quotes if quote.supplier_id == supplier_id]
    for quote in quotes_to_delete:
        if quote.id is not None:
            quote_repo.delete(quote.id)

    return supplier_repo.delete(supplier_id)


# Competitor Management Functions
def get_all_competitors(repo: SQLModelRepository[Competitor]) -> list[Competitor]:
    return repo.get_all()


def get_competitor_by_id(repo: SQLModelRepository[Competitor], competitor_id: int) -> Competitor | None:
    return repo.get(competitor_id)


def save_competitor(repo: SQLModelRepository[Competitor], competitor_data: Competitor) -> Competitor:
    if competitor_data.id is None:
        return repo.add(competitor_data)
    else:
        update_data = competitor_data.model_dump(exclude_unset=True, exclude={'id', 'created_at', 'updated_at'})
        updated_competitor = repo.update(competitor_data.id, update_data)
        if updated_competitor is None:
            raise ValueError(f"Competitor with id {competitor_data.id} not found for update.")
        return updated_competitor


def delete_competitor(competitor_repo: SQLModelRepository[Competitor], bid_repo: SQLModelRepository[Bid],
                      competitor_id: int) -> bool:
    # TODO: Consider adding a filter method to SQLModelRepository for efficiency
    all_bids = bid_repo.get_all()
    bids_to_delete = [bid for bid in all_bids if bid.competitor_id == competitor_id]
    for bid in bids_to_delete:
        if bid.id is not None:
            bid_repo.delete(bid.id)

    return competitor_repo.delete(competitor_id)


# Quote Management Functions
def get_quotes_by_item_id(repo: SQLModelRepository[Quote], item_id: int) -> list[Quote]:
    # TODO: Consider adding a filter method to SQLModelRepository for efficiency
    all_quotes = repo.get_all()
    return [quote for quote in all_quotes if quote.item_id == item_id]


def add_quote(repo: SQLModelRepository[Quote], quote_data: Quote) -> Quote:
    return repo.add(quote_data)


# Bid Management Functions
def get_bids_by_item_id(repo: SQLModelRepository[Bid], item_id: int) -> list[Bid]:
    # TODO: Consider adding a filter method to SQLModelRepository for efficiency
    all_bids = repo.get_all()
    return [bid for bid in all_bids if bid.item_id == item_id]


def add_bid(repo: SQLModelRepository[Bid], bid_data: Bid) -> Bid:
    return repo.add(bid_data)
