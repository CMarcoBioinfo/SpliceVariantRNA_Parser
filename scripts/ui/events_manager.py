from scripts.core.utils import is_number, parse_position

class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}

    # ---------------------------------------------------------
    # RECONSTRUCTION DES LIGNES (identique à ton code d’origine)
    # ---------------------------------------------------------
    def build_table_values(self, category):
        evs = self.events_by_cat.get(category) or []
        cols = self.columns_by_cat.get(category) or []

        return [
            [ev.get(col + "_fmt", ev.get(col, "")) for col in cols]
            for ev in evs
        ]

    # ---------------------------------------------------------
    # TRI (identique à ton code d’origine, mais centralisé)
    # ---------------------------------------------------------
    def sort_category(self, category, col_index):
        cols = self.columns_by_cat.get(category) or []
        if not cols:
            return []

        col_name = cols[col_index]
        ev_list = self.events_by_cat.get(category) or []

        numeric = all(is_number(ev.get(col_name)) for ev in ev_list)
        sort_key = f"{category}_{col_name}"
        reverse = self.sort_states.get(sort_key, 0)

        if numeric:
            ev_list.sort(key=lambda ev: ev.get(col_name, float("inf")), reverse=bool(reverse))
        elif col_name.lower() == "position":
            ev_list.sort(key=lambda ev: parse_position(ev.get(col_name, "")), reverse=bool(reverse))
        else:
            ev_list.sort(key=lambda ev: str(ev.get(col_name, "")).lower(), reverse=bool(reverse))

        self.sort_states[sort_key] = 1 - reverse

        return self.build_table_values(category)
