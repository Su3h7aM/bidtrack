import pandas as pd
from db.models import (
    Quote,
    Bid,
    Supplier,
    Bidder, # Renamed from Competitor
)  # Assuming models are accessible like this


def get_quotes_dataframe(
    quotes_list: list[Quote], suppliers_list: list[Supplier]
) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for quotes.

    Args:
        quotes_list: A list of Quote objects.
        suppliers_list: A list of Supplier objects.

    Returns:
        A pandas DataFrame with quote data, including supplier names and formatted dates.
    """
    if not quotes_list:
        return pd.DataFrame(
            columns=["supplier_name", "price", "created_at", "update_at", "notes"]
        )

    quotes_df = pd.DataFrame([q.model_dump() for q in quotes_list])

    if not quotes_df.empty and suppliers_list:
        supplier_map = {s.id: s.name for s in suppliers_list}
        quotes_df["supplier_name"] = quotes_df["supplier_id"].map(supplier_map)

    if "created_at" in quotes_df.columns:
        quotes_df["created_at"] = pd.to_datetime(quotes_df["created_at"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if "update_at" in quotes_df.columns:
        # Ensure 'update_at' exists and is not all NaT before formatting
        if pd.notnull(quotes_df["update_at"]).all():
            quotes_df["update_at"] = pd.to_datetime(quotes_df["update_at"]).dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            quotes_df["update_at"] = None  # Or some other placeholder like '-' or ''

    # Convert to numeric, coercing errors and filling NaNs
    # These fields are Decimal in the model, pandas usually converts them to object or float.
    # Explicit conversion ensures they are numeric for calculations.
    quotes_df['price'] = pd.to_numeric(quotes_df['price'], errors='coerce').fillna(0.0)
    quotes_df['freight'] = pd.to_numeric(quotes_df['freight'], errors='coerce').fillna(0.0)
    quotes_df['additional_costs'] = pd.to_numeric(quotes_df['additional_costs'], errors='coerce').fillna(0.0)
    quotes_df['taxes'] = pd.to_numeric(quotes_df['taxes'], errors='coerce').fillna(0.0) # This is I (%)
    quotes_df['margin'] = pd.to_numeric(quotes_df['margin'], errors='coerce').fillna(0.0) # This is L (%)

    total_direct_cost = quotes_df['price'] + quotes_df['freight'] + quotes_df['additional_costs']
    # Ensure taxes and margin are treated as percentages (e.g., 6 for 6%)
    total_percentage_sum_decimal = (quotes_df['taxes'] / 100) + (quotes_df['margin'] / 100)
    denominator = 1 - total_percentage_sum_decimal

    # Initialize calculated_price column with pd.NA
    quotes_df['calculated_price'] = pd.NA 

    # Calculate only where denominator is valid ( > 0 to avoid division by zero or negative/zero price if sum_percentages >= 100%)
    valid_denominator_mask = denominator > 0
    quotes_df.loc[valid_denominator_mask, 'calculated_price'] = total_direct_cost[valid_denominator_mask] / denominator[valid_denominator_mask]
    
    # Select and reorder columns for consistency
    display_columns = [
        "supplier_name", # Derived
        "price", # Original: price (model) -> price (df)
        "freight",
        "additional_costs",
        "taxes",
        "margin",
        "calculated_price", # Derived
        "created_at", # Original: created_at (model) -> created_at (df)
        "update_at",  # Original: update_at (model) -> update_at (df)
        "notes",
        "id",
        "item_id",
        "supplier_id", # Original: supplier_id (model) -> supplier_id (df)
    ]
    # Filter out columns not present in quotes_df to avoid KeyError
    # (e.g. if a quote_list was empty and columns were predefined differently)
    
    # Ensure all display_columns exist, adding them with pd.NA if not
    for col_name in display_columns:
        if col_name not in quotes_df.columns:
            quotes_df[col_name] = pd.NA

    # Ensure the DataFrame has all display_columns in the correct order
    # and filters out any columns not in display_columns
    quotes_df = quotes_df.reindex(columns=display_columns)

    return quotes_df


def get_bids_dataframe(
    bids_list: list[Bid], bidders_list: list[Bidder] # Renamed parameter
) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for bids.

    Args:
        bids_list: A list of Bid objects.
        bidders_list: A list of Bidder objects. # Renamed parameter

    Returns:
        A pandas DataFrame with bid data, including bidder names and formatted dates. # Updated docstring
    """
    if not bids_list:
        return pd.DataFrame(
            columns=["bidder_name", "price", "created_at", "notes", "update_at"]
        )

    bids_df = pd.DataFrame([b.model_dump() for b in bids_list])

    # Ensure 'bidder_name' column is always present
    if not bids_df.empty:
        if bidders_list:  # Check if bidders_list is provided and not empty
            bidder_map = {b.id: b.name for b in bidders_list}
            if "bidder_id" in bids_df.columns:
                bids_df["bidder_name"] = bids_df["bidder_id"].map(bidder_map)
                bids_df["bidder_name"] = bids_df["bidder_name"].fillna("N/D")
            else:
                # If bidder_id column does not exist, fill bidder_name with "N/D"
                bids_df["bidder_name"] = "N/D"
        else:
            # If bidders_list is empty or not provided, fill bidder_name with "N/D"
            bids_df["bidder_name"] = "N/D"
    # If bids_df is empty, the initial check for bids_list already handles returning a DataFrame with bidder_name

    if "created_at" in bids_df.columns:
        bids_df["created_at"] = pd.to_datetime(bids_df["created_at"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if "update_at" in bids_df.columns:
        # Ensure 'update_at' exists and is not all NaT before formatting
        if pd.notnull(bids_df["update_at"]).all():  # Check if not all values are NaT
            bids_df["update_at"] = pd.to_datetime(bids_df["update_at"]).dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            # Handle cases where 'update_at' might be all NaT or mixed; decide on a representation
            bids_df["update_at"] = None  # Or some other placeholder

    # Select and reorder columns for consistency
    # Note: 'bidding_id' is also part of Bid model, include if needed for other purposes
    display_columns = [
        "bidder_name", # Derived
        "price",
        "created_at",
        "update_at",
        "notes",
        "id",
        "item_id",
        "bidding_id", # Original: bidding_id (model) -> bidding_id (df)
        "bidder_id",  # Original: bidder_id (model) -> bidder_id (df)
    ]
    # Filter out columns not present in bids_df to avoid KeyError

    # Ensure all display_columns exist, adding them with pd.NA if not
    for col_name in display_columns:
        if col_name not in bids_df.columns:
            bids_df[col_name] = pd.NA

    # Ensure the DataFrame has all display_columns in the correct order
    # and filters out any columns not in display_columns
    bids_df = bids_df.reindex(columns=display_columns)

    return bids_df
