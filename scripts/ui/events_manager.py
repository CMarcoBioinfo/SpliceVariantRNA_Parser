from scripts.core.utils import is_number, parse_position

class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}   # mémorise asc/desc par colonne
        self.filters = {}       # filtres actifs par catégorie/colonne

    # ---------------------------------------------------------
    # CONSTRUCTION DES LIGNES DU TABLEAU
    # ---------------------------------------------------------
    def build_table_values(self, category, ev_list=None):
        """
        Construit les lignes du tableau :
        - ligne 0 = filtres
        - lignes suivantes = événements (filtrés ou non)
        """
        if ev_list is None:
            ev_list = self.events_by_cat.get(category) or []

        cols = self.columns_by_cat.get(category) or []

        # Ligne 0 = filtres
        filter_row = ["[ filtre ]" for _ in cols]

        # Lignes normales
        rows = [
            [ev.get(col + "_fmt", ev.get(col, "")) for col in cols]
            for ev in ev_list
        ]

        return [filter_row] + rows

    # ---------------------------------------------------------
    # EXTRACTION DES DÉTAILS
    # ---------------------------------------------------------
    def extract_details(self, category, idx):
        """
        Retourne les détails d'un événement sélectionné.
        La ligne 0 est la ligne de filtres → pas de détails.
        """
        ev_list = self.apply_filters(category)

        if idx == 0:
            return ""  # ligne de filtres

        real_idx = idx - 1  # décalage car ligne 0 = filtres

        if real_idx < 0 or real_idx >= len(ev_list):
            return ""

        ev = ev_list[real_idx]

        detail_keys = [
            "Gene", "Event", "Position", "Depth", "PSI-like",
            "Distribution", "p-value", "Significative",
            "nbSignificantSamples", "nbFilteredSamples",
            "cStart", "cEnd", "HGVS", "Source"
        ]

        return "\n".join(
            f"{k}: {ev[k]}" for k in detail_keys if k in ev
        )

    # ---------------------------------------------------------
    # TRI
    # ---------------------------------------------------------
    def sort_category(self, category, col_index):
        """
        Trie les événements filtrés selon la colonne cliquée.
        Retourne les valeurs prêtes à afficher (avec ligne 0).
        """
        cols = self.columns_by_cat.get(category) or []
        if not cols:
            return []

        col_name = cols[col_index]

        # On trie toujours sur les données filtrées
        ev_list = self.apply_filters(category)

        # Détection du type de tri
        numeric = all(is_number(ev.get(col_name)) for ev in ev_list)

        # Toggle asc/desc
        sort_key = f"{category}_{col_name}"
        reverse = self.sort_states.get(sort_key, 0)

        # Tri numérique
        if numeric:
            ev_list.sort(
                key=lambda ev: ev.get(col_name, float("inf")),
                reverse=bool(reverse)
            )

        # Tri position génomique
        elif col_name.lower() == "position":
            ev_list.sort(
                key=lambda ev: parse_position(ev.get(col_name, "")),
                reverse=bool(reverse)
            )

        # Tri texte
        else:
            ev_list.sort(
                key=lambda ev: str(ev.get(col_name, "")).lower(),
                reverse=bool(reverse)
            )

        # Inversion pour prochain clic
        self.sort_states[sort_key] = 1 - reverse

        # Retourne les lignes triées + ligne 0
        return self.build_table_values(category, ev_list)

    # ---------------------------------------------------------
    # GESTION DES FILTRES
    # ---------------------------------------------------------
    def add_filter(self, category, col_name, value, op="contains", mode="AND"):
        """
        Ajoute un filtre avancé :
        - op : opérateur (contains, =, >, <, etc.)
        - value : valeur du filtre
        - mode : AND/OR entre filtres de la même colonne
        """
        if not value:
            return

        cat_filters = self.filters.setdefault(category, {})
        col_filters = cat_filters.setdefault(col_name, [])

        col_filters.append({
            "op": op,
            "value": value,
            "mode": mode
        })

    def clear_filters(self, category, col_name=None):
        """Efface les filtres d'une colonne ou de toute la catégorie."""
        if category not in self.filters:
            return

        if col_name is None:
            self.filters[category] = {}
        else:
            self.filters[category].pop(col_name, None)

    def get_filters(self, category):
        return self.filters.get(category, {})


    # ---------------------------------------------------------
    # APPLICATION DES FILTRES
    # ---------------------------------------------------------
    def apply_filters(self, category):
        """
        Retourne la liste des événements filtrés.
        - AND global entre colonnes
        - AND/OR configurable entre filtres d'une même colonne
        """
        evs = self.events_by_cat.get(category) or []
        cat_filters = self.filters.get(category, {})

        if not cat_filters:
            return evs

        filtered = []

        for ev in evs:
            keep_event = True

            for col_name, filters in cat_filters.items():
                if not filters:
                    continue

                ev_val = str(ev.get(col_name, "")).lower()
                col_keep = None

                for f in filters:
                    value = f["value"].lower()
                    mode = f["mode"]
                    match = value in ev_val

                    if col_keep is None:
                        col_keep = match
                    else:
                        col_keep = (col_keep and match) if mode == "AND" else (col_keep or match)

                if not col_keep:
                    keep_event = False
                    break

            if keep_event:
                filtered.append(ev)

        return filtered

    # ---------------------------------------------------------
    # ÉVALUATION D’UN FILTRE (ÉTAPE 2)
    # ---------------------------------------------------------
    def evaluate_filter(self, ev_val, f):
        """
        Applique un filtre simple à une valeur de colonne.
        Étape 2 : uniquement texte + numérique basique.
        """
        op = f["op"]
        value = f["value"]

        # Normalisation texte
        ev_val_str = str(ev_val).lower()
        value_str = str(value).lower()

        # -----------------------------
        # Opérateurs TEXTUELS
        # -----------------------------
        if op == "contains":
            return value_str in ev_val_str

        if op == "startswith":
            return ev_val_str.startswith(value_str)

        if op == "endswith":
            return ev_val_str.endswith(value_str)

        if op == "=":
            return ev_val_str == value_str

        if op == "!=":
            return ev_val_str != value_str

        # -----------------------------
        # Opérateurs NUMÉRIQUES
        # -----------------------------
        try:
            ev_num = float(ev_val)
            val_num = float(value)

            if op == ">":
                return ev_num > val_num
            if op == "<":
                return ev_num < val_num
            if op == ">=":
                return ev_num >= val_num
            if op == "<=":
                return ev_num <= val_num
            if op == "=":
                return ev_num == val_num
            if op == "!=":
                return ev_num != val_num

        except:
            # Si conversion impossible → pas un filtre numérique
            return False

        return False
