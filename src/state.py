import streamlit as st


def initialize_session_state():
    """Initializes all session state variables for the application."""

    # IDs Selecionados
    if "selected_bidding_id" not in st.session_state:
        st.session_state.selected_bidding_id = None
    if "selected_item_id" not in st.session_state:
        st.session_state.selected_item_id = None

    # Nomes para exibição (para evitar re-lookup constante se o ID já está no estado)
    if "selected_bidding_name_for_display" not in st.session_state:
        st.session_state.selected_bidding_name_for_display = None
    if "selected_item_name_for_display" not in st.session_state:
        st.session_state.selected_item_name_for_display = None

    # Estado para controlar abertura de diálogos e edição
    for dialog_type in ["bidding", "item", "supplier", "competitor"]:
        if f"show_manage_{dialog_type}_dialog" not in st.session_state:
            st.session_state[f"show_manage_{dialog_type}_dialog"] = False
        if f"editing_{dialog_type}_id" not in st.session_state:
            st.session_state[f"editing_{dialog_type}_id"] = None
        if f"confirm_delete_{dialog_type}" not in st.session_state:
            st.session_state[f"confirm_delete_{dialog_type}"] = False

    if "parent_bidding_id_for_item_dialog" not in st.session_state:
        st.session_state.parent_bidding_id_for_item_dialog = None
