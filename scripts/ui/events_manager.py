class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}   # 🔥 indispensable pour le toggle de tri

    def build_table_values(self, category):
        evs = self.events_by_cat.get(category) or []
        cols = self.columns_by_cat.get(category) or []

        return [
            [ev.get(col + "_fmt", ev.get(col, "")) for col in cols]
            for ev in evs
        ]

    def extract_details(self, category, idx):
        ev_list = self.events_by_cat.get(category) or []
        if idx < 0 or idx >= len(ev_list):
            return ""

        ev = ev_list[idx]

        detail_keys = [
            "Gene", "Event", "Position", "Depth", "PSI-like",
            "Distribution", "p-value", "Significative",
            "nbSignificantSamples", "nbFilteredSamples",
            "cStart", "cEnd", "HGVS", "Source"
        ]

        return "\n".join(
            f"{k}: {ev[k]}" for k in detail_keys if k in ev
        )

    def sort_category(self, category, col_index):
        # Récupération des colonnes
        cols = self.columns_by_cat.get(category) or []
        if not cols:
            return []
    
        # Nom de la colonne cliquée
        col_name = cols[col_index]
    
        # Liste des événements à trier
        ev_list = self.events_by_cat.get(category) or []
    
        # Détection du type de tri
        numeric = all(is_number(ev.get(col_name)) for ev in ev_list)
    
        # Gestion du toggle asc/desc
        sort_key = f"{category}_{col_name}"
        reverse = self.sort_states.get(sort_key, 0)
    
        # --- Tri numérique ---
        if numeric:
            ev_list.sort(
                key=lambda ev: ev.get(col_name, float("inf")),
                reverse=bool(reverse)
            )
    
        # --- Tri position ---
        elif col_name.lower() == "position":
            ev_list.sort(
                key=lambda ev: parse_position(ev.get(col_name, "")),
                reverse=bool(reverse)
            )
    
        # --- Tri texte ---
        else:
            ev_list.sort(
                key=lambda ev: str(ev.get(col_name, "")).lower(),
                reverse=bool(reverse)
            )
    
        # Toggle pour le prochain clic
        self.sort_states[sort_key] = 1 - reverse
    
        # Reconstruction des lignes (ÉTAPE 1)
        return self.build_table_values(category)

