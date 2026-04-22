class EventsManager:
    def __init__(self, events_by_cat, columns_by_cat):
        self.events_by_cat = events_by_cat
        self.columns_by_cat = columns_by_cat

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
