import pandas as pd
from decimal import Decimal, InvalidOperation
from db.models import (
    Quote,
    Bid,
    Supplier,
    Bidder,
    Item # Added Item for get_quotes_dataframe
)


def get_quotes_dataframe(
    quotes_list: list[Quote],
    suppliers_list: list[Supplier],
    items_list: list[Item] # Added items_list
) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for quotes.

    Args:
        quotes_list: A list of Quote objects.
        suppliers_list: A list of Supplier objects.
        items_list: A list of Item objects.

    Returns:
        A pandas DataFrame with quote data, including supplier names, item names,
        calculated_price, and formatted dates.
    """
    if not quotes_list:
        # Define columns based on expected output, including new ones
        return pd.DataFrame(
            columns=[
                "id", "item_id", "supplier_id", "price", "freight", "additional_costs",
                "taxes", "margin", "notes", "created_at", "updated_at",
                "supplier_name", "item_name", "calculated_price"
            ]
        )

    quotes_df = pd.DataFrame([q.model_dump() for q in quotes_list])

    # Map supplier names
    if not quotes_df.empty and suppliers_list:
        supplier_map = {s.id: s.name for s in suppliers_list}
        quotes_df["supplier_name"] = quotes_df["supplier_id"].map(supplier_map).fillna("Fornecedor Desconhecido")
    elif not quotes_df.empty:
        quotes_df["supplier_name"] = "Fornecedor Desconhecido"

    # Map item names
    if not quotes_df.empty and items_list:
        item_map = {i.id: i.name for i in items_list}
        quotes_df["item_name"] = quotes_df["item_id"].map(item_map).fillna("Item Desconhecido")
    elif not quotes_df.empty:
        quotes_df["item_name"] = "Item Desconhecido"

    # Convert date columns to datetime objects (naive)
    if "created_at" in quotes_df.columns:
        quotes_df["created_at"] = pd.to_datetime(quotes_df["created_at"], errors='coerce').dt.tz_localize(None)
    if "updated_at" in quotes_df.columns:
        quotes_df["updated_at"] = pd.to_datetime(quotes_df["updated_at"], errors='coerce').dt.tz_localize(None)

    # Calculate 'calculated_price' using Decimal for precision
    # Ensure necessary columns are present and are of Decimal type for calculation
    cols_for_calc = ['price', 'freight', 'additional_costs', 'taxes', 'margin']
    for col in cols_for_calc:
        if col not in quotes_df.columns:
            quotes_df[col] = Decimal('0.0') # Add column if missing, initialize to 0
        else:
            # Convert to Decimal, handling potential errors from various input types
            def to_decimal_safe(value):
                if isinstance(value, Decimal):
                    return value
                if value is None:
                    return Decimal('0.0')
                try:
                    return Decimal(str(value))
                except (InvalidOperation, TypeError, ValueError):
                    return Decimal('NaN') # Use NaN for values that cannot be converted
            quotes_df[col] = quotes_df[col].apply(to_decimal_safe)
            # Replace NaN with 0 for calculation, or decide how to handle rows with bad data
            quotes_df[col] = quotes_df[col].replace(Decimal('NaN'), Decimal('0.0'))


    # Calculation logic from ui/quote_tab_content.py (assumed correct)
    base_price = quotes_df['price']
    freight = quotes_df['freight']
    additional_costs = quotes_df['additional_costs']
    taxes_percentage = quotes_df['taxes']
    margin_percentage = quotes_df['margin']

    price_with_freight_costs = base_price + freight + additional_costs
    taxes_value = price_with_freight_costs * (taxes_percentage / Decimal(100))
    price_before_margin = price_with_freight_costs + taxes_value
    margin_value = price_before_margin * (margin_percentage / Decimal(100))
    quotes_df['calculated_price'] = price_before_margin + margin_value
    
    # Define all columns expected by the UI or for general use
    # This ensures consistency in column order and presence.
    final_columns = [
        "id", "item_name", "supplier_name", "price", "freight", "additional_costs",
        "taxes", "margin", "calculated_price", "notes",
        "item_id", "supplier_id", "created_at", "updated_at"
    ]
    
    # Ensure all final_columns exist, adding them with pd.NA or appropriate defaults if not
    for col_name in final_columns:
        if col_name not in quotes_df.columns:
            if col_name in ["price", "freight", "additional_costs", "taxes", "margin", "calculated_price"]:
                 quotes_df[col_name] = Decimal('0.0') # Or pd.NA if preferred for non-calculated numeric
            else:
                 quotes_df[col_name] = pd.NA

    # Reorder and select final columns
    quotes_df = quotes_df.reindex(columns=final_columns)

    return quotes_df


def get_bids_dataframe(
    bids_list: list[Bid],
    bidders_list: list[Bidder],
    items_list: list[Item] # Added items_list
) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for bids.

    Args:
        bids_list: A list of Bid objects.
        bidders_list: A list of Bidder objects.
        items_list: A list of Item objects.

    Returns:
        A pandas DataFrame with bid data, including bidder names, item names, and formatted dates.
    """
    if not bids_list:
        return pd.DataFrame(
            columns=[
                "id", "item_id", "bidding_id", "bidder_id", "price", "notes",
                "created_at", "updated_at", "item_name", "bidder_name"
            ]
        )

    bids_df = pd.DataFrame([b.model_dump() for b in bids_list])

    # Map bidder names
    if not bids_df.empty and bidders_list:
        bidder_map = {b.id: b.name for b in bidders_list}
        bids_df["bidder_name"] = bids_df["bidder_id"].map(bidder_map)
        # Handle cases where bidder_id might be None or not in map
        bids_df["bidder_name"] = bids_df.apply(
            lambda row: "Licitante Desconhecido" if pd.isna(row["bidder_id"]) else bidder_map.get(row["bidder_id"], "Licitante Desconhecido"),
            axis=1
        )
    elif not bids_df.empty:
         bids_df["bidder_name"] = "Licitante Desconhecido"


    # Map item names
    if not bids_df.empty and items_list:
        item_map = {i.id: i.name for i in items_list}
        bids_df["item_name"] = bids_df["item_id"].map(item_map).fillna("Item Desconhecido")
    elif not bids_df.empty:
        bids_df["item_name"] = "Item Desconhecido"


    # Convert date columns to datetime objects (naive)
    if "created_at" in bids_df.columns:
        bids_df["created_at"] = pd.to_datetime(bids_df["created_at"], errors='coerce').dt.tz_localize(None)
    if "updated_at" in bids_df.columns:
        bids_df["updated_at"] = pd.to_datetime(bids_df["updated_at"], errors='coerce').dt.tz_localize(None)

    # Ensure 'price' is Decimal
    if 'price' in bids_df.columns:
        bids_df['price'] = bids_df['price'].apply(lambda x: Decimal(str(x)) if x is not None else Decimal('0.0'))
    else:
        bids_df['price'] = Decimal('0.0')


    final_columns = [
        "id", "item_name", "bidder_name", "price", "notes",
        "item_id", "bidding_id", "bidder_id", "created_at", "updated_at"
    ]

    for col_name in final_columns:
        if col_name not in bids_df.columns:
            if col_name == "price":
                bids_df[col_name] = Decimal('0.0')
            else:
                bids_df[col_name] = pd.NA

    bids_df = bids_df.reindex(columns=final_columns)

    return bids_df
