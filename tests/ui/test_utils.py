import pytest
from unittest.mock import MagicMock # Or namedtuple for simple objects

from ui.utils import get_options_map # Corrected import
# Import BiddingMode to get its value for the test, but avoid direct enum member access in test data
# if the metadata issue is still present.
from db.models import BiddingMode # Corrected import

# Simple mock object for testing
class MockObject:
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

def test_get_options_map_empty_list():
    options_map, ids_list = get_options_map([], default_message="Empty")
    assert options_map == {None: "Empty"}
    assert ids_list == [None]

def test_get_options_map_simple_objects():
    data = [
        MockObject(id=1, name="Option 1"),
        MockObject(id=2, name="Option 2"),
    ]
    options_map, ids_list = get_options_map(data, default_message="Select...")

    expected_map = {None: "Select...", 1: "Option 1", 2: "Option 2"}
    expected_ids = [None, 1, 2]

    assert options_map == expected_map
    assert ids_list == expected_ids

def test_get_options_map_with_name_col():
    # Using a different attribute for the name
    data = [
        MockObject(id='a', name="Unused Name A", title="Title A"), # Added name
        MockObject(id='b', name="Unused Name B", title="Title B"), # Added name
    ]
    options_map, ids_list = get_options_map(data, name_col="title")

    expected_map = {None: "Selecione...", 'a': "Title A", 'b': "Title B"}
    expected_ids = [None, 'a', 'b']

    assert options_map == expected_map
    assert ids_list == expected_ids


def test_get_options_map_with_extra_cols():
    data = [
        MockObject(id=1, name="Bidding Alpha", city="New York", process_number="P001"),
        MockObject(id=2, name="Project Beta", city="London", process_number="P002"),
    ]
    options_map, ids_list = get_options_map(data, extra_cols=["city", "process_number"])

    expected_map = {
        None: "Selecione...",
        1: "New York - P001",
        2: "London - P002"
    }
    expected_ids = [None, 1, 2]

    assert options_map == expected_map
    assert ids_list == expected_ids

def test_get_options_map_with_extra_cols_and_enum_workaround():
    # Using string value directly as a workaround for potential Enum metadata issues during test collection
    # Defaulting to actual enum value, but test will use string if direct access fails
    national_competition_value = BiddingMode.PE.value # Using an actual valid enum member
    try:
        # This line is mostly to ensure BiddingMode itself is usable.
        # The actual value passed to MockObject will be the string.
        if not isinstance(BiddingMode.PE, BiddingMode): # A bit of a tautology to use the Enum
             national_competition_value = "Pregão Eletrônico" # Fallback if BiddingMode.PE is not BiddingMode
    except AttributeError: # If BiddingMode.PE itself is not accessible due to metadata issues
        national_competition_value = "Pregão Eletrônico"


    data = [
        MockObject(id=1, name="Bidding Gamma", city="Paris", mode=national_competition_value, process_number="P003"),
    ]
    options_map, ids_list = get_options_map(data, extra_cols=["city", "process_number", "mode"])

    expected_map = {
        None: "Selecione...",
        1: f"Paris - P003 ({national_competition_value})"
    }
    expected_ids = [None, 1]

    assert options_map == expected_map
    assert ids_list == expected_ids

def test_get_options_map_with_missing_extra_col_attribute():
    data = [
        MockObject(id=1, name="Bidding Delta", city="Tokyo"), # Missing 'process_number'
    ]
    options_map, ids_list = get_options_map(data, extra_cols=["city", "process_number"])

    expected_map = {
        None: "Selecione...",
        1: "Tokyo - [process_number?]"
    }
    expected_ids = [None, 1]

    assert options_map == expected_map
    assert ids_list == expected_ids

def test_get_options_map_no_id_attribute():
    class NoIdObject:
        def __init__(self, name):
            self.name = name

    data = [NoIdObject("No ID Object")]
    options_map, ids_list = get_options_map(data)
    assert options_map == {None: "Selecione..."}
    assert ids_list == [None]

def test_get_options_map_one_extra_col():
    data = [
        MockObject(id=1, name="Only City", city="Berlin"),
    ]
    options_map, ids_list = get_options_map(data, extra_cols=["city"])
    expected_map = {
        None: "Selecione...",
        1: "Berlin"
    }
    expected_ids = [None, 1]
    assert options_map == expected_map
    assert ids_list == expected_ids

def test_get_options_map_name_col_fallback_if_extra_cols_empty_processed():
    data = [
        MockObject(id=1, name="Fallback Name")
    ]
    options_map, ids_list = get_options_map(data, extra_cols=["city", "process_number"])
    expected_map = {
        None: "Selecione...",
        1: "[city?] - [process_number?]"
    }
    assert options_map[1] == expected_map[1]

    data_with_name = [MockObject(id=1, name="Unused Name", my_name_attr="Specific Name")] # Added name
    options_map_named, _ = get_options_map(data_with_name, name_col="my_name_attr", extra_cols=["non_existent_col1", "non_existent_col2"])
    assert options_map_named[1] == "[non_existent_col1?] - [non_existent_col2?]"

    options_map_name_only, _ = get_options_map(data_with_name, name_col="my_name_attr", extra_cols=None)
    assert options_map_name_only[1] == "Specific Name"
