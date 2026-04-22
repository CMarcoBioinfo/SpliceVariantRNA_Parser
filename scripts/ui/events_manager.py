from scripts.core.utils import is_number, parse_position

class EventsManager:
    """
    Gère les opérations sur les événements :
    - reconstruction des lignes
    - tri
    - extraction des détails
    """

    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}

    # ------------------------------------------------------------------
    # RECONSTRUCTION DES LIGNES (comme avant, mais propre)
    # ------------------------------------------------------------------
    def build_table_values(self, category):
        evs = self.events_by_cat.get(category) or []
        cols = self.columns_by_cat.get(category) or []

        return [
            [ev.get(col + "_fmt", ev.get(col, "")) for col in cols]
            for ev in evs
        ]

    # ------------------------------------------------------------------
    # TRI (propre, centralisé)
    # ------------------------------------------------------------------
    def sort_category(self, category, col_name):
        ev_list = self.events_by_cat.get(category) or []
        sort_key = f"{category}_{col_name}"
        reverse = bool(self.sort_states.get(sort_key, 0))

        numeric = all(is_number(ev.get(col_name)) for ev in ev_list)

        if numeric:
            ev_list.sort(key=lambda ev: ev.get(col_name, float("inf")), reverse=reverse)
        elif col_name.lower() == "position":
            ev_list.sort(key=lambda ev: parse_position(ev.get(col_name, "")), reverse=reverse)
        else:
            ev_list.sort(key=lambda ev: str(ev.get(col_name, "")).lower(), reverse=reverse)

        self.sort_states[sort_key] = 1 - self.sort_states.get(sort_key, 0)

        return self.build_table_values(category)

    # ------------------------------------------------------------------
    # DÉTAILS
    # ------------------------------------------------------------------
    def extract_details(self, category, idx):
        ev = self.events_by_cat.get(category, [])[idx]

        detail_keys = [
            "Gene", "Event", "Position", "Depth", "PSI-like",
            "Distribution", "p-value", "Significative",
            "nbSignificantSamples", "nbFilteredSamples",
            "cStart", "cEnd", "HGVS", "Source"
        ]

        return "\n".join(f"{k}: {ev[k]}" for k in detail_keys if k in ev)

