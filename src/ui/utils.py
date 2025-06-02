from typing import Any


# --- Funções Auxiliares para Selectbox ---
def get_options_map(
    data_list: list[Any],
    name_col: str = "name",
    extra_cols: list[str] | None = None,
    default_message: str = "Selecione...",
) -> tuple[dict[Any, str], list[Any]]:
    if not data_list:
        return {None: default_message}, [None]

    options_map: dict[Any, str] = {None: default_message}
    ids_list: list[Any] = [None]

    for row in data_list:
        row_id = getattr(row, "id", None)  # Ensure row has id
        if row_id is None:
            continue  # Skip if no id

        display_name_parts = []
        if extra_cols:
            try:
                for col in extra_cols:
                    if hasattr(row, col):
                        display_name_parts.append(str(getattr(row, col)))
                    else:  # Add a placeholder if an expected extra_col is missing
                        display_name_parts.append(f"[{col}?]")

                # Construct display name from parts
                if len(display_name_parts) >= 2:
                    display_name = f"{display_name_parts[0]} - {display_name_parts[1]}"
                    if len(display_name_parts) > 2:
                        display_name += f" ({display_name_parts[2]})"
                elif len(display_name_parts) == 1:
                    display_name = display_name_parts[0]
                else:  # Fallback if no extra_cols were actually processed
                    display_name = str(row_id)

            except AttributeError:  # Fallback in case of unexpected error
                display_name = str(row_id)
        elif hasattr(row, name_col):
            display_name = str(getattr(row, name_col))
        else:
            display_name = str(row_id)  # Fallback if name_col attribute is missing

        options_map[row_id] = display_name
        ids_list.append(row_id)

    return options_map, ids_list
