import pandas as pd
from db.models import Quote, Bid, Supplier, Competitor # Assuming models are accessible like this

def get_quotes_dataframe(quotes_list: list[Quote], suppliers_list: list[Supplier]) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for quotes.

    Args:
        quotes_list: A list of Quote objects.
        suppliers_list: A list of Supplier objects.

    Returns:
        A pandas DataFrame with quote data, including supplier names and formatted dates.
    """
    if not quotes_list:
        return pd.DataFrame(columns=['supplier_name', 'price', 'created_at', 'update_at', 'notes'])

    quotes_df = pd.DataFrame([q.model_dump() for q in quotes_list])

    if not quotes_df.empty and suppliers_list:
        supplier_map = {s.id: s.name for s in suppliers_list}
        quotes_df['supplier_name'] = quotes_df['supplier_id'].map(supplier_map)

    if 'created_at' in quotes_df.columns:
        quotes_df['created_at'] = pd.to_datetime(quotes_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'update_at' in quotes_df.columns:
        # Ensure 'update_at' exists and is not all NaT before formatting
        if pd.notnull(quotes_df['update_at']).all():
            quotes_df['update_at'] = pd.to_datetime(quotes_df['update_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            quotes_df['update_at'] = None # Or some other placeholder like '-' or ''

    # Select and reorder columns for consistency
    display_columns = ['supplier_name', 'price', 'margin', 'created_at', 'update_at', 'notes', 'id', 'item_id', 'supplier_id']
    # Filter out columns not present in quotes_df to avoid KeyError
    final_columns = [col for col in display_columns if col in quotes_df.columns]
    quotes_df = quotes_df[final_columns]

    return quotes_df

def get_bids_dataframe(bids_list: list[Bid], competitors_list: list[Competitor]) -> pd.DataFrame:
    """
    Creates and preprocesses a DataFrame for bids.

    Args:
        bids_list: A list of Bid objects.
        competitors_list: A list of Competitor objects.

    Returns:
        A pandas DataFrame with bid data, including competitor names and formatted dates.
    """
    if not bids_list:
        return pd.DataFrame(columns=['competitor_name', 'price', 'created_at', 'notes', 'update_at'])

    bids_df = pd.DataFrame([b.model_dump() for b in bids_list])

    if not bids_df.empty and competitors_list:
        competitor_map = {c.id: c.name for c in competitors_list}
        bids_df['competitor_name'] = bids_df['competitor_id'].map(competitor_map)

    if 'created_at' in bids_df.columns:
        bids_df['created_at'] = pd.to_datetime(bids_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'update_at' in bids_df.columns:
        # Ensure 'update_at' exists and is not all NaT before formatting
        if pd.notnull(bids_df['update_at']).all(): # Check if not all values are NaT
            bids_df['update_at'] = pd.to_datetime(bids_df['update_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Handle cases where 'update_at' might be all NaT or mixed; decide on a representation
            bids_df['update_at'] = None # Or some other placeholder

    # Select and reorder columns for consistency
    # Note: 'bidding_id' is also part of Bid model, include if needed for other purposes
    display_columns = ['competitor_name', 'price', 'created_at', 'notes', 'update_at', 'id', 'item_id', 'bidding_id', 'competitor_id']
    # Filter out columns not present in bids_df to avoid KeyError
    final_columns = [col for col in display_columns if col in bids_df.columns]
    bids_df = bids_df[final_columns]

    return bids_df
