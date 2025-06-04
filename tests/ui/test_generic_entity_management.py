import pytest
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal
from unittest.mock import MagicMock, call
from decimal import Decimal, InvalidOperation # Keep InvalidOperation for context, though ConversionSyntax is actual

# Modules to test
from ui.generic_entity_management import ( # Corrected import
    load_and_prepare_data,
    display_search_box_and_filter_df,
    handle_save_changes,
)
from db.models import BiddingMode # Corrected import

# --- Fixtures ---

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_st(mocker):
    mock_st_obj = MagicMock()
    # Patching the correct location now that imports within the module under test are also src-relative
    mocker.patch('ui.generic_entity_management.st', mock_st_obj)
    return mock_st_obj

# --- Tests for load_and_prepare_data ---

def test_load_and_prepare_data_empty(mock_repo, mock_st):
    mock_repo.get_all.return_value = []
    df = load_and_prepare_data(mock_repo, "TestEntity")
    assert df.empty
    mock_st.info.assert_called_once_with("Nenhum(a) testentity cadastrado(a).")

def test_load_and_prepare_data_with_data(mock_repo, mock_st):
    class MockEntity:
        def __init__(self, id, name, created_at, updated_at=None):
            self.id = id
            self.name = name
            self.created_at = created_at
            self.updated_at = updated_at

        def model_dump(self): # SQLModel compatibility
            return self.__dict__

    sample_data = [
        MockEntity(1, "Entity1", pd.Timestamp("2023-01-01 10:00:00"), pd.Timestamp("2023-01-02 11:00:00")),
        MockEntity(2, "Entity2", pd.Timestamp("2023-01-03 12:00:00"), None),
    ]
    mock_repo.get_all.return_value = sample_data

    df = load_and_prepare_data(mock_repo, "TestEntity")

    assert not df.empty
    assert len(df) == 2
    assert 'id' in df.columns
    assert 'name' in df.columns
    assert pd.api.types.is_datetime64_ns_dtype(df['created_at'])
    assert pd.api.types.is_datetime64_ns_dtype(df['updated_at'])
    assert df.loc[df['id'] == 1, 'name'].iloc[0] == "Entity1"
    assert df['created_at'].iloc[0].tzinfo is None
    assert df['updated_at'].iloc[0].tzinfo is None


def test_load_and_prepare_data_with_columns_to_display(mock_repo, mock_st):
    class MockEntity:
        def __init__(self, id, name, extra_field, created_at):
            self.id = id
            self.name = name
            self.extra_field = extra_field
            self.created_at = created_at
        def model_dump(self): return self.__dict__

    sample_data = [MockEntity(1, "E1", "Extra1", pd.Timestamp("2023-01-01"))]
    mock_repo.get_all.return_value = sample_data

    df = load_and_prepare_data(mock_repo, "TestEntity", columns_to_display=['id', 'name', 'new_col'])

    assert_frame_equal(df, pd.DataFrame({
        'id': [1],
        'name': ['E1'],
        'new_col': [None],
    }), check_dtype=False)

# --- Tests for display_search_box_and_filter_df ---

def test_display_search_box_empty_df(mock_st):
    empty_df = pd.DataFrame({'col1': []})
    result_df = display_search_box_and_filter_df(empty_df, ['col1'], "key_suffix", "Entities")
    assert_frame_equal(result_df, empty_df)
    mock_st.text_input.assert_not_called()

def test_display_search_box_no_search_term(mock_st):
    data = {'name': ['Alice', 'Bob'], 'city': ['Amsterdam', 'Berlin']}
    df = pd.DataFrame(data)
    mock_st.text_input.return_value = ""

    result_df = display_search_box_and_filter_df(df, ['name', 'city'], "key", "People")
    assert_frame_equal(result_df, df)

def test_display_search_box_with_search_term(mock_st):
    data = {'name': ['Alice', 'Bob', 'Charlie'], 'city': ['Amsterdam', 'Berlin', 'Cairo']}
    df = pd.DataFrame(data)
    mock_st.text_input.return_value = "Alice"

    result_df = display_search_box_and_filter_df(df, ['name'], "key", "People")
    expected_df = pd.DataFrame({'name': ['Alice'], 'city': ['Amsterdam']})
    assert_frame_equal(result_df.reset_index(drop=True), expected_df.reset_index(drop=True))

def test_display_search_box_case_insensitive(mock_st):
    data = {'name': ['Alice', 'Bob'], 'city': ['Amsterdam', 'Berlin']}
    df = pd.DataFrame(data)
    mock_st.text_input.return_value = "alice"

    result_df = display_search_box_and_filter_df(df, ['name'], "key", "People")
    expected_df = pd.DataFrame({'name': ['Alice'], 'city': ['Amsterdam']})
    assert_frame_equal(result_df.reset_index(drop=True), expected_df.reset_index(drop=True))

def test_display_search_box_multiple_columns(mock_st):
    data = {'name': ['Alice', 'Bob'], 'city': ['Amsterdam', 'Berlin']}
    df = pd.DataFrame(data)
    mock_st.text_input.return_value = "Berlin"

    result_df = display_search_box_and_filter_df(df, ['name', 'city'], "key", "People")
    expected_df = pd.DataFrame({'name': ['Bob'], 'city': ['Berlin']})
    assert_frame_equal(result_df.reset_index(drop=True), expected_df.reset_index(drop=True))

def test_display_search_box_no_match(mock_st):
    data = {'name': ['Alice', 'Bob'], 'city': ['Amsterdam', 'Berlin']}
    df = pd.DataFrame(data)
    mock_st.text_input.return_value = "Zzz"

    result_df = display_search_box_and_filter_df(df, ['name', 'city'], "key", "People")
    assert result_df.empty
    mock_st.info.assert_called_with("Nenhum resultado encontrado para sua busca em People.")

# --- Tests for handle_save_changes ---

@pytest.fixture
def sample_original_df():
    # Using string values for BiddingMode as a workaround for potential metadata/import issues in tests
    return pd.DataFrame({
        'id': [1, 2],
        'name': ['Original Name 1', 'Original Name 2'],
        'value': [Decimal('10.0'), Decimal('20.0')],
        # Ensure ID 1 has a different status_display/status_code than what test_handle_save_special_conversion will change it to
        'status_display': [BiddingMode.PP.value, BiddingMode.PE.value],
        'status_code': [BiddingMode.PP, BiddingMode.PE],
        'created_at': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
        'updated_at': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')]
    })

def test_handle_save_no_changes(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'value', 'status_display']
    )
    assert not result
    mock_repo.update.assert_not_called()
    mock_st.info.assert_any_call("Nenhuma alteração detectada para salvar em entitys.")

def test_handle_save_simple_value_change(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'name'] = "Updated Name 1"

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'value']
    )
    assert result
    mock_repo.update.assert_called_once_with(1, {'name': "Updated Name 1"})
    mock_st.success.assert_called_once_with("Entity ID 1 atualizado(a) com sucesso.")

def test_handle_save_required_field_empty(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'name'] = ""

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'value'],
        required_fields=['name']
    )
    assert result
    mock_repo.update.assert_not_called()
    mock_st.error.assert_called_once_with("Entity ID 1: Campo obrigatório 'name' (destino: 'name') está vazio. Alterações não salvas.")

def test_handle_save_decimal_conversion(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'value'] = "15.50"

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'value'],
        decimal_fields=['value']
    )
    assert result
    mock_repo.update.assert_called_once_with(1, {'value': Decimal('15.50')})

def test_handle_save_decimal_conversion_invalid(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'value'] = "invalid_decimal"

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'value'],
        decimal_fields=['value']
    )
    assert result
    mock_repo.update.assert_not_called()
    mock_st.error.assert_called_once_with("Entity ID 1: Valor inválido para campo decimal 'value' ('invalid_decimal'): [<class 'decimal.ConversionSyntax'>].")

def test_handle_save_special_conversion(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'status_display'] = BiddingMode.PE.value

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['status_display'],
        special_conversions={
            'status_display': {'target_field': 'status_code', 'conversion_func': BiddingMode}
        }
    )
    assert result
    mock_repo.update.assert_called_once_with(1, {'status_code': BiddingMode.PE})

def test_handle_save_fields_to_remove(mock_repo, mock_st, sample_original_df):
    edited_df = sample_original_df.copy()
    edited_df.loc[edited_df['id'] == 1, 'name'] = "Updated Name"
    edited_df.loc[edited_df['id'] == 1, 'status_display'] = "Some New Display"

    result = handle_save_changes(
        sample_original_df, edited_df, mock_repo, "Entity",
        editable_columns=['name', 'status_display'],
        fields_to_remove_before_update=['status_display']
    )
    assert result
    mock_repo.update.assert_called_once_with(1, {'name': "Updated Name"})

def test_handle_save_no_id_column(mock_repo, mock_st):
    original_df_no_id = pd.DataFrame({'name': ['A']})
    edited_df_no_id = pd.DataFrame({'name': ['B']})
    result = handle_save_changes(
        original_df_no_id, edited_df_no_id, mock_repo, "Entity",
        editable_columns=['name']
    )
    assert not result
    mock_st.error.assert_called_with("Coluna 'id' não encontrada no DataFrame original de Entity. Não é possível salvar alterações.")

def test_handle_save_change_from_value_to_nan_and_back(mock_repo, mock_st):
    original_df = pd.DataFrame({
        'id': [1], 'optional_field': [Decimal('100.0')], 'created_at': [pd.Timestamp('2023-01-01')]
    })
    edited_df_to_nan = original_df.copy()
    edited_df_to_nan.loc[0, 'optional_field'] = None

    result1 = handle_save_changes(
        original_df, edited_df_to_nan, mock_repo, "Entity",
        editable_columns=['optional_field'], decimal_fields=['optional_field']
    )
    assert result1
    mock_repo.update.assert_called_once_with(1, {'optional_field': None})
    mock_st.success.assert_called_with("Entity ID 1 atualizado(a) com sucesso.")

    mock_repo.reset_mock()
    mock_st.reset_mock()

    original_df_is_nan = pd.DataFrame({
        'id': [1], 'optional_field': [None], 'created_at': [pd.Timestamp('2023-01-01')]
    })
    edited_df_from_nan = original_df_is_nan.copy()
    edited_df_from_nan.loc[0, 'optional_field'] = Decimal('50.0')

    result2 = handle_save_changes(
        original_df_is_nan, edited_df_from_nan, mock_repo, "Entity",
        editable_columns=['optional_field'], decimal_fields=['optional_field']
    )
    assert result2
    mock_repo.update.assert_called_once_with(1, {'optional_field': Decimal('50.0')})
    mock_st.success.assert_called_with("Entity ID 1 atualizado(a) com sucesso.")

def test_handle_save_datetime_comparison_precision(mock_repo, mock_st):
    original_df = pd.DataFrame({
        'id': [1],
        'event_time': [pd.Timestamp('2023-01-01 10:00:00.123456')],
        'created_at': [pd.Timestamp('2023-01-01')]
    })
    edited_df_same_time = original_df.copy()

    result_no_change = handle_save_changes(
        original_df, edited_df_same_time, mock_repo, "Entity",
        editable_columns=['event_time']
    )
    assert not result_no_change
    mock_repo.update.assert_not_called()

    edited_df_microsecond_change = original_df.copy()
    edited_df_microsecond_change.loc[0, 'event_time'] = pd.Timestamp('2023-01-01 10:00:00.123457')

    result_change = handle_save_changes(
        original_df, edited_df_microsecond_change, mock_repo, "Entity",
        editable_columns=['event_time']
    )
    assert result_change
    mock_repo.update.assert_called_once_with(1, {'event_time': pd.Timestamp('2023-01-01 10:00:00.123457')})
    mock_st.success.assert_called_with("Entity ID 1 atualizado(a) com sucesso.")
