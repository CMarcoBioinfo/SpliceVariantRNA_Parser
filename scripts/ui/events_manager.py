from scripts.core.utils import is_number, parse_position

class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat
        self.sort_states = {}
        self.filters = {}   # {category: {col_name: [ {conditions: [...], mode: AND}, ... ]}}

    # ---------------------------------------------------------
    # TABLE
    # ---------------------------------------------------------
    def build_table_values(self, category, ev_list=None):
        if ev_list is None:
            ev_list = self.events_by_cat.get(category) or []

        cols = self.columns_by_cat.get(category) or []
        filter_row = ["[ filtre ]" for _ in cols]

        rows = [
            [ev.get(col + "_fmt", ev.get(col, "")) for col in cols]
            for ev in ev_list
        ]

        return [filter_row] + rows

    # ---------------------------------------------------------
    # DETAILS
    # ---------------------------------------------------------
    def extract_details(self, category, idx):
        ev_list = self.apply_filters(category)
        if idx == 0:
            return ""

        real_idx = idx - 1
        if real_idx < 0 or real_idx >= len(ev_list):
            return ""

        ev = ev_list[real_idx]

        detail_keys = [
            "Gene", "Event", "Position", "Depth", "PSI-like",
            "Distribution", "p-value", "Significative",
            "nbSignificantSamples", "nbFilteredSamples",
            "cStart", "cEnd", "HGVS", "Source"
        ]

        return "\n".join(f"{k}: {ev[k]}" for k in detail_keys if k in ev)

    # ---------------------------------------------------------
    # TRI
    # ---------------------------------------------------------
    def sort_category(self, category, col_index):
        cols = self.columns_by_cat.get(category) or []
        if not cols:
            return []

        col_name = cols[col_index]
        ev_list = self.apply_filters(category)

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
        return self.build_table_values(category, ev_list)

    # ---------------------------------------------------------
    # GESTION DES GROUPES DE FILTRES
    # ---------------------------------------------------------
    def add_filter_group(self, category, col_name):
        cat_filters = self.filters.setdefault(category, {})
        col_filters = cat_filters.setdefault(col_name, [])

        col_filters.append({
            "conditions": [],
            "mode": "AND"
        })

    def add_condition(self, category, col_name, group_index, op, value):
        self.filters[category][col_name][group_index]["conditions"].append({
            "op": op,
            "value": value
        })

    def remove_condition(self, category, col_name, group_index, cond_index):
        del self.filters[category][col_name][group_index]["conditions"][cond_index]

    def get_filters(self, category):
        return self.filters.get(category, {})

    # ---------------------------------------------------------
    # APPLICATION DES FILTRES (NOUVELLE VERSION)
    # ---------------------------------------------------------
    def apply_filters(self, category):
        evs = self.events_by_cat.get(category) or []
        cat_filters = self.filters.get(category, {})

        if not cat_filters:
            return evs

        filtered = []

        for ev in evs:
            keep_event = True

            for col_name, groups in cat_filters.items():
                if not groups:
                    continue

                ev_val = ev.get(col_name, "")
                col_keep = True

                # AND entre groupes
                for group in groups:
                    group_match = False

                    # OR internes
                    for cond in group["conditions"]:
                        if self.evaluate_filter(ev_val, cond):
                            group_match = True
                            break

                    if not group_match:
                        col_keep = False
                        break

                if not col_keep:
                    keep_event = False
                    break

            if keep_event:
                filtered.append(ev)

        return filtered

    # ---------------------------------------------------------
    # ÉVALUATION D’UNE CONDITION
    # ---------------------------------------------------------
    def evaluate_filter(self, ev_val, cond):
        op = cond["op"]
        value = cond["value"]

        ev_val_str = str(ev_val).lower()
        value_str = str(value).lower()

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

        try:
            ev_num = float(ev_val)
            val_num = float(value)

            if op == ">": return ev_num > val_num
            if op == "<": return ev_num < val_num
            if op == ">=": return ev_num >= val_num
            if op == "<=": return ev_num <= val_num
            if op == "=": return ev_num == val_num
            if op == "!=": return ev_num != val_num

        except:
            return False

        return False
