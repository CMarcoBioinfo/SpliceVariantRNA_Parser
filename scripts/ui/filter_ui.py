import PySimpleGUI as sg

class FilterUI:
    def __init__(self, events_manager):
        self.manager = events_manager

    def open_filter_popup(self, parent_window, category, col_name, saved_position=None):
        """Popup dynamique : ne se ferme pas lors de ADD/DEL."""

        # --- Position d'ouverture ---
        if saved_position is not None:
            popup_location = saved_position
        else:
            wx, wy = parent_window.current_location()
            ww, wh = parent_window.size
            popup_location = (wx + ww // 2, wy + wh // 2)

        # --- Fonction pour formater les filtres ---
        def format_filters():
            lst = []
            for f in self.manager.get_filters(category).get(col_name, []):
                bullet = "•" if f["mode"] == "AND" else "○"
                lst.append(f'{bullet} {f["op"]} "{f["value"]}" ({f["mode"]})')
            return lst

        # --- Layout dynamique ---
        layout = [
            [sg.Text(f"Filtre pour {col_name}", font=("Arial", 12, "bold"))],
            [sg.Text("Opérateur :"), sg.Combo(
                ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="],
                default_value="contains",
                key="-OP-"
            )],
            [sg.Text("Valeur :"), sg.Input(key="-VAL-")],
            [sg.Button("+ Ajouter", key="-ADD-")],

            [sg.Text("Filtres actifs :")],
            [sg.Listbox(values=format_filters(), key="-FILTERS-", size=(40, 6))],
            [sg.Button("Supprimer", key="-DEL-")],

            [sg.Text("Mode entre filtres :")],
            [
                sg.Radio("AND", "MODE", default=True, key="-MODE-AND-"),
                sg.Radio("OR", "MODE", default=False, key="-MODE-OR-")
            ],

            [sg.Button("Appliquer"), sg.Button("Fermer")]
        ]

        popup = sg.Window(
            f"Filtre {col_name}",
            layout,
            modal=True,
            keep_on_top=True,
            finalize=True,
            disable_close=True,
            location=popup_location,
            enable_window_configure_events=True
        )

        changed = False
        last_position = popup_location

        # --- Boucle popup ---
        while True:
            ev, vals = popup.read()

            # Mise à jour position
            if ev == "-Configure-":
                last_position = popup.current_location()
                continue

            # Fermer
            if ev == "Fermer":
                popup.close()
                return False, last_position

            # Appliquer
            if ev == "Appliquer":
                popup.close()
                return changed, last_position

            # Ajouter un filtre
            if ev == "-ADD-":
                op = vals["-OP-"]
                val = vals["-VAL-"]
                mode = "AND" if vals["-MODE-AND-"] else "OR"

                if val:
                    self.manager.add_filter(category, col_name, val, op=op, mode=mode)
                    popup["-FILTERS-"].update(values=format_filters())
                    changed = True

            # Supprimer un filtre
            if ev == "-DEL-":
                selected = vals["-FILTERS-"]
                if selected:
                    filters = format_filters()
                    idx = filters.index(selected[0])
                    self.manager.filters[category][col_name].pop(idx)
                    popup["-FILTERS-"].update(values=format_filters())
                    changed = True
