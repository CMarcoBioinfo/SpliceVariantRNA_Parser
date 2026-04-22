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
