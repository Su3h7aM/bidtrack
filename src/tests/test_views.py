import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, date

import unittest
from unittest.mock import MagicMock, patch # Removed new_callable from here
import pandas as pd
from datetime import datetime, date

# Real Pydantic Models for creating sample data returned by mocked repositories
# These imports must be distinct from the models potentially mocked within views.py's scope
from src.db.models import (
    Bidding as RealBidding,
    Item as RealItem,
    Supplier as RealSupplier,
    Competitor as RealCompetitor,
    Quote as RealQuote,
    Bid as RealBid,
    BiddingMode as RealBiddingMode
)


class TestViewFunctions(unittest.TestCase):

    def common_mock_st_config(self, mock_st):
        """Helper to configure common streamlit mocks."""
        mock_st.sidebar.columns.return_value = (MagicMock(), MagicMock())
        mock_st.subheader = MagicMock()
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.dataframe = MagicMock()
        mock_st.sidebar.header = MagicMock()
        mock_st.sidebar.selectbox = MagicMock(return_value="Todas")
        mock_st.sidebar.multiselect = MagicMock(return_value=[])

        mock_sidebar_col1 = MagicMock()
        mock_sidebar_col2 = MagicMock()
        mock_sidebar_col1.date_input.return_value = date(2023,1,1)
        mock_sidebar_col2.date_input.return_value = date(2023,12,31)
        mock_st.sidebar.columns.return_value = (mock_sidebar_col1, mock_sidebar_col2)

        mock_st.sidebar.text_input = MagicMock(return_value="")
        return mock_st

    @patch('src.ui.views.st')
    # @patch('src.ui.views.BiddingMode', new_callable=MagicMock) # Removed: BiddingMode is an Enum, not a SQLModel table causing issues
    @patch('src.ui.views.Bid', new_callable=MagicMock)
    @patch('src.ui.views.Quote', new_callable=MagicMock)
    @patch('src.ui.views.Competitor', new_callable=MagicMock)
    @patch('src.ui.views.Supplier', new_callable=MagicMock)
    @patch('src.ui.views.Item', new_callable=MagicMock)
    @patch('src.ui.views.Bidding', new_callable=MagicMock)
    def test_render_licitacoes_tab_runs_without_error(self, mock_bidding_class, mock_item_class, mock_supplier_class, mock_competitor_class, mock_quote_class, mock_bid_class, mock_st): # Removed mock_bidding_mode_enum
        from src.ui.views import render_licitacoes_tab # Import here, after patches are active
        mock_st = self.common_mock_st_config(mock_st)

        bidding_repo_mock = MagicMock()
        sample_bidding_data = [
            RealBidding(id=1, process_number='001/2023', city='City A', mode=RealBiddingMode.PE, date=datetime(2023,1,10,10,0,0), created_at=datetime.now(), updated_at=datetime.now(), description="Desc A"),
            RealBidding(id=2, process_number='002/2023', city='City B', mode=RealBiddingMode.PP, date=datetime(2023,1,15,11,0,0), created_at=datetime.now(), updated_at=datetime.now(), description="Desc B"), # Changed CC to PP
        ]
        bidding_repo_mock.get_all.return_value = sample_bidding_data

        try:
            render_licitacoes_tab(bidding_repo_mock)
        except Exception as e:
            self.fail(f"render_licitacoes_tab raised an exception: {e}")

        bidding_repo_mock.get_all.assert_called_once()
        mock_st.dataframe.assert_called()

    @patch('src.ui.views.st')
    # @patch('src.ui.views.BiddingMode', new_callable=MagicMock)
    @patch('src.ui.views.Bid', new_callable=MagicMock)
    @patch('src.ui.views.Quote', new_callable=MagicMock)
    @patch('src.ui.views.Competitor', new_callable=MagicMock)
    @patch('src.ui.views.Supplier', new_callable=MagicMock)
    @patch('src.ui.views.Item', new_callable=MagicMock)
    @patch('src.ui.views.Bidding', new_callable=MagicMock)
    def test_render_licitacoes_tab_no_data(self, mock_bidding_class, mock_item_class, mock_supplier_class, mock_competitor_class, mock_quote_class, mock_bid_class, mock_st): # Removed mock_bidding_mode_enum
        from src.ui.views import render_licitacoes_tab # Import here
        mock_st = self.common_mock_st_config(mock_st)
        bidding_repo_mock = MagicMock()
        bidding_repo_mock.get_all.return_value = []
        try:
            render_licitacoes_tab(bidding_repo_mock)
        except Exception as e:
            self.fail(f"render_licitacoes_tab (no data) raised an exception: {e}")
        bidding_repo_mock.get_all.assert_called_once()
        mock_st.info.assert_called_with("Nenhuma licitação cadastrada.")

    @patch('src.ui.views.st')
    # @patch('src.ui.views.BiddingMode', new_callable=MagicMock)
    @patch('src.ui.views.Bid', new_callable=MagicMock)
    @patch('src.ui.views.Quote', new_callable=MagicMock)
    @patch('src.ui.views.Competitor', new_callable=MagicMock)
    @patch('src.ui.views.Supplier', new_callable=MagicMock)
    @patch('src.ui.views.Item', new_callable=MagicMock)
    @patch('src.ui.views.Bidding', new_callable=MagicMock)
    def test_render_itens_tab_runs_without_error(self, mock_bidding_class, mock_item_class, mock_supplier_class, mock_competitor_class, mock_quote_class, mock_bid_class, mock_st): # Removed mock_bidding_mode_enum
        from src.ui.views import render_itens_tab # Import here
        mock_st = self.common_mock_st_config(mock_st)

        item_repo_mock = MagicMock()
        bidding_repo_mock = MagicMock()

        sample_bidding_data = [
            RealBidding(id=1, process_number='P001', city='City X', date=datetime(2023,2,10), created_at=datetime.now(), updated_at=datetime.now(), mode=RealBiddingMode.PE, description="Bidding for items"),
        ]
        bidding_repo_mock.get_all.return_value = sample_bidding_data

        sample_item_data = [
            RealItem(id=10, bidding_id=1, name="Item A", desc="Description A", quantity=10, unit="UN", created_at=datetime.now(), updated_at=datetime.now()),
            RealItem(id=11, bidding_id=1, name="Item B", desc="Description B", quantity=5, unit="CX", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        item_repo_mock.get_all.return_value = sample_item_data

        try:
            render_itens_tab(item_repo_mock, bidding_repo_mock)
        except Exception as e:
            self.fail(f"render_itens_tab raised an exception: {e}")

        item_repo_mock.get_all.assert_called_once()
        bidding_repo_mock.get_all.assert_called_once()
        mock_st.dataframe.assert_called()

    @patch('src.ui.views.st')
    # @patch('src.ui.views.BiddingMode', new_callable=MagicMock)
    @patch('src.ui.views.Bid', new_callable=MagicMock)
    @patch('src.ui.views.Quote', new_callable=MagicMock)
    @patch('src.ui.views.Competitor', new_callable=MagicMock)
    @patch('src.ui.views.Supplier', new_callable=MagicMock)
    @patch('src.ui.views.Item', new_callable=MagicMock)
    @patch('src.ui.views.Bidding', new_callable=MagicMock)
    def test_render_orcamentos_tab_runs_without_error(self, mock_bidding_class, mock_item_class, mock_supplier_class, mock_competitor_class, mock_quote_class, mock_bid_class, mock_st): # Removed mock_bidding_mode_enum
        from src.ui.views import render_orcamentos_tab # Import here
        mock_st = self.common_mock_st_config(mock_st)

        quote_repo_mock = MagicMock()
        item_repo_mock = MagicMock()
        supplier_repo_mock = MagicMock()

        sample_item_data = [
            RealItem(id=10, bidding_id=1, name="Item A", desc="Description A", quantity=10, unit="UN", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        item_repo_mock.get_all.return_value = sample_item_data

        sample_supplier_data = [
            RealSupplier(id=20, name="Supplier X", email="sx@test.com", phone="123", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        supplier_repo_mock.get_all.return_value = sample_supplier_data

        sample_quote_data = [
            RealQuote(id=30, item_id=10, supplier_id=20, price=100.50, margin=0.2, notes="Note Q1", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        quote_repo_mock.get_all.return_value = sample_quote_data

        try:
            render_orcamentos_tab(quote_repo_mock, item_repo_mock, supplier_repo_mock)
        except Exception as e:
            self.fail(f"render_orcamentos_tab raised an exception: {e}")

        quote_repo_mock.get_all.assert_called_once()
        item_repo_mock.get_all.assert_called_once()
        supplier_repo_mock.get_all.assert_called_once()
        mock_st.dataframe.assert_called()

    @patch('src.ui.views.st')
    # @patch('src.ui.views.BiddingMode', new_callable=MagicMock)
    @patch('src.ui.views.Bid', new_callable=MagicMock)
    @patch('src.ui.views.Quote', new_callable=MagicMock)
    @patch('src.ui.views.Competitor', new_callable=MagicMock)
    @patch('src.ui.views.Supplier', new_callable=MagicMock)
    @patch('src.ui.views.Item', new_callable=MagicMock)
    @patch('src.ui.views.Bidding', new_callable=MagicMock)
    def test_render_lances_tab_runs_without_error(self, mock_bidding_class, mock_item_class, mock_supplier_class, mock_competitor_class, mock_quote_class, mock_bid_class, mock_st): # Removed mock_bidding_mode_enum
        from src.ui.views import render_lances_tab # Import here
        mock_st = self.common_mock_st_config(mock_st)

        bid_repo_mock = MagicMock()
        item_repo_mock = MagicMock()
        competitor_repo_mock = MagicMock()

        sample_item_data = [
            RealItem(id=10, bidding_id=1, name="Item A", desc="Description A", quantity=10, unit="UN", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        item_repo_mock.get_all.return_value = sample_item_data

        sample_competitor_data = [
            RealCompetitor(id=40, name="Competitor Y", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        competitor_repo_mock.get_all.return_value = sample_competitor_data

        sample_bid_data = [
            RealBid(id=50, item_id=10, competitor_id=40, bidding_id=1, price=90.00, notes="Note B1", created_at=datetime.now(), updated_at=datetime.now()),
        ]
        bid_repo_mock.get_all.return_value = sample_bid_data

        try:
            render_lances_tab(bid_repo_mock, item_repo_mock, competitor_repo_mock)
        except Exception as e:
            self.fail(f"render_lances_tab raised an exception: {e}")

        bid_repo_mock.get_all.assert_called_once()
        item_repo_mock.get_all.assert_called_once()
        competitor_repo_mock.get_all.assert_called_once()
        mock_st.dataframe.assert_called()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
