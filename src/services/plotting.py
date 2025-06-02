import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# --- Funções Auxiliares para Gráficos ---
def create_quotes_figure(quotes_df_display: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        quotes_df_display,
        x="supplier_name",  # English column name
        y="calculated_price", # English column name
        title="Comparativo de Preços de Venda dos Orçamentos", 
        labels={ # English keys, Portuguese values
            "supplier_name": "Fornecedor", 
            "calculated_price": "Preço Calculado (R$)",
            "price": "Preço Base (R$)", # For hover data
            "freight": "Frete (R$)", # For hover data
            "additional_costs": "Custos Adicionais (R$)", # For hover data
            "taxes": "Impostos (%)", # For hover data
            "margin": "Margem (%)" # For hover data
        }, 
        color="supplier_name",  # English column name
        text_auto=True,
    )
    fig.update_layout(
        xaxis_title="Fornecedor", # Already Portuguese
        yaxis_title="Preço Calculado (R$)", # Already Portuguese
        legend_title_text="Fornecedores", # Already Portuguese
        dragmode="pan",
        showlegend=False,
    )  # Added showlegend=False
    return fig


def create_bids_figure(
    bids_df_display: pd.DataFrame, min_quote_price: float | None
) -> go.Figure:
    if (
        "created_at" in bids_df_display.columns # English column name
        and not bids_df_display["created_at"].isnull().all()
    ):
        b_df_sorted = (
            bids_df_display.sort_values(by="created_at") # English column name
            if len(bids_df_display) > 1
            else bids_df_display
        )
        fig = px.line(
            b_df_sorted,
            x="created_at",       # English column name
            y="price",            # English column name
            color="bidder_name",  # English column name
            title="Evolução dos Lances ao Longo do Tempo",
            labels={ # English keys, Portuguese values
                "created_at": "Momento do Lance",
                "price": "Preço do Lance (R$)",
                "bidder_name": "Licitante",
            },
            markers=True,
        )
    else:
        fig = px.bar(
            bids_df_display,
            x="bidder_name",  # English column name
            y="price",        # English column name
            title="Comparativo de Preços dos Lances (sem timestamp)",
            labels={ # English keys, Portuguese values
                "bidder_name": "Licitante", 
                "price": "Preço do Lance (R$)"
            }, 
            color="bidder_name",  # English column name
            text_auto=True,
        )
    fig.update_layout(
        dragmode="pan", legend_title_text="Licitantes", showlegend=False # Already Portuguese
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
