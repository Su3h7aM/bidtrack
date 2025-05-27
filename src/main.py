import streamlit as st


st.set_page_config(layout="wide", page_title="BidTrack - Gerenciamento de Licitações")

pages = {
    "📊 Área de Análises": [
        st.Page("pages/analyze_biddings.py", title="Licitações"),
        st.Page("pages/analyze_items.py", title="Itens"),
    ],
    "📝 Área de Cadastros": [
        st.Page("pages/manage_suppliers.py", title="Fornecedores"),
        st.Page("pages/manage_quotes.py", title="Orçamentos"),
        st.Page("pages/manage_competitors.py", title="Concorrentes"),
        st.Page("pages/manage_bids.py", title="Lances"),
    ],
}

pg = st.navigation(pages)
pg.run()
