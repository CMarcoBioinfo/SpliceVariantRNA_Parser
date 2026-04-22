from scripts.core.utils import is_number, parse_position

class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}
        self.filters = {}

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
        ev_list = self.apply_filters(category)
    
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

    def add_filter(self, category, col_name, value, mode="AND"):
        if not value:
            return

        cat_filters = self.filters.setdefault(category, {})
        col_filters = cat_filters.setdefault(col_name, [])

        col_filters.append({"value": value, "mode": mode})

    def clear_filters(self, category, col_name=None):
        if category not in self.filters:
            return

        if col_name is None:
            # on efface tous les filtres de la catégorie
            self.filters[category] = {}
        else:
            self.filters[category].pop(col_name, None)

    def get_filters(self, category):
        return self.filters.get(category, {})

    def apply_filters(self, category):
        """
        Version avancée :
        - plusieurs filtres par colonne
        - AND/OR entre filtres d'une même colonne
        - AND global entre colonnes
        """
        evs = self.events_by_cat.get(category) or []
        cat_filters = self.filters.get(category, {})

        if not cat_filters:
            return evs

        filtered = []

        for ev in evs:
            keep_event = True

            # AND global entre colonnes
            for col_name, filters in cat_filters.items():
                if not filters:
                    continue

                ev_val = str(ev.get(col_name, "")).lower()

                # Évalue les filtres de cette colonne
                col_keep = None

                for f in filters:
                    value = f["value"].lower()
                    mode = f["mode"]

                    match = value in ev_val

                    if col_keep is None:
                        col_keep = match
                    else:
                        if mode == "AND":
                            col_keep = col_keep and match
                        else:  # OR
                            col_keep = col_keep or match

                # Si une colonne échoue → l'événement est rejeté
                if not col_keep:
                    keep_event = False
                    break

            if keep_event:
                filtered.append(ev)

        return filtered

