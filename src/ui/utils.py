from typing import Any # For type hinting # Removed Optional, List, Dict, Tuple

# --- Funções Auxiliares para Selectbox ---
def get_options_map(data_list: list[Any], name_col: str = 'name', extra_cols: list[str] | None = None, default_message:str = "Selecione...") -> tuple[dict[int | str | None, str], list[int | str | None]]:
    if not data_list:
        # Ensure the structure matches the return type hint even for default case
        return {None: default_message}, [None]

    options_map: dict[int | str | None, str] = {None: default_message}
    ids_list: list[int | str | None] = [None]

    for row in data_list:
        row_id: int | str | None = getattr(row, 'id', None) # Ensure row_id is typed for clarity
        if row_id is None:
            continue

        display_name_parts = []
        if extra_cols:
            try:
                for col in extra_cols:
                    if hasattr(row, col):
                        display_name_parts.append(str(getattr(row, col)))
                    else:
                        display_name_parts.append(f"[{col}?]")

                current_display_name = "" # Renamed to avoid conflict with outer scope if any
                if len(display_name_parts) >= 2:
                    current_display_name = f"{display_name_parts[0]} - {display_name_parts[1]}"
                    if len(display_name_parts) > 2:
                         current_display_name += f" ({display_name_parts[2]})"
                elif len(display_name_parts) == 1:
                    current_display_name = display_name_parts[0]
                else:
                    current_display_name = str(row_id)

                options_map[row_id] = current_display_name

            except AttributeError:
                options_map[row_id] = str(row_id)
        elif hasattr(row, name_col):
            options_map[row_id] = str(getattr(row, name_col))
        else:
            options_map[row_id] = str(row_id)

        ids_list.append(row_id)

    return options_map, ids_list
