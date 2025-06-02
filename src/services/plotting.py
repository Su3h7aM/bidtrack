import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# --- Funções Auxiliares para Gráficos ---
def create_quotes_figure(quotes_df_display: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        quotes_df_display,
        x="supplier_name",
        y="calculated_price", # Changed from "price"
        title="Comparativo de Preços de Venda dos Orçamentos", # Updated title
        labels={"supplier_name": "Fornecedor", "calculated_price": "Preço de Venda Calculado (R$)"}, # Updated label
        color="supplier_name",
        text_auto=True,
    )
    fig.update_layout(
        xaxis_title="Fornecedor",
        yaxis_title="Preço de Venda Calculado (R$)", # Updated label
        legend_title_text="Fornecedores",
        dragmode="pan",
        showlegend=False,
    )  # Added showlegend=False
    return fig


def create_bids_figure(
    bids_df_display: pd.DataFrame, min_quote_price: float | None
) -> go.Figure:
    if (
        "created_at" in bids_df_display.columns
        and not bids_df_display["created_at"].isnull().all()
    ):
        b_df_sorted = (
            bids_df_display.sort_values(by="created_at")
            if len(bids_df_display) > 1
            else bids_df_display
        )
        fig = px.line(
            b_df_sorted,
            x="created_at",
            y="price",
            color="bidder_name", # Renamed from competitor_name
            title="Evolução dos Lances ao Longo do Tempo",
            labels={
                "created_at": "Momento do Lance",
                "price": "Preço do Lance (R$)",
                "bidder_name": "Licitante", # Renamed key and value
            },
            markers=True,
        )
    else:
        fig = px.bar(
            bids_df_display,
            x="bidder_name", # Renamed from competitor_name
            y="price",
            title="Comparativo de Preços dos Lances (sem timestamp)",
            labels={"bidder_name": "Licitante", "price": "Preço do Lance (R$)"}, # Renamed key and value
            color="bidder_name", # Renamed from competitor_name
            text_auto=True,
        )
    fig.update_layout(
        dragmode="pan", legend_title_text="Licitantes", showlegend=False # Renamed legend title
    )  # Added showlegend=False
    if min_quote_price is not None:
        fig.add_hline(
            y=min_quote_price,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Menor Orçamento: R${min_quote_price:,.2f}",
            annotation_position="bottom right",
            annotation_font_size=10,
            annotation_font_color="red",
        )
    return fig
