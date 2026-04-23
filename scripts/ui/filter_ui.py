import PySimpleGUI as sg

class FilterUI:
    """Gère l'UI des filtres : popup, opérateurs, suppression, etc."""
    def __init__(self, events_manager):
        self.manager = events_manager

    def open_filter_popup(self, parent_window, category, col_name, saved_position=None):
        """Retourne (changed, new_position)."""

        existing_filters = self.manager.get_filters(category).get(col_name, [])
        ops = ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="]

        # --- Position d'ouverture ---
        if saved_position is not None:
            popup_location = saved_position
        else:
            wx, wy = parent_window.current_location()
            ww, wh = parent_window.size
            popup_location = (wx + ww // 2, wy + wh // 2)

        # --- Fonction pour reconstruire le layout ---
        def build_layout():
            layout = [
                [sg.Text(f"Filtre pour {col_name}", font=("Arial", 12, "bold"))],
                [sg.Text("Opérateur :"), sg.Combo(ops, default_value="contains", key="-OP-")],
                [sg.Text("Valeur :"), sg.Input(key="-VAL-")],
                [sg.Button("+ Ajouter", key="-ADD-")],
                [sg.Text("Filtres actifs :")],
            ]

            for i, f in enumerate(existing_filters):
                bullet = "•" if f["mode"] == "AND" else "○"
                txt = f'{bullet} {f["op"]} "{f["value"]}" ({f["mode"]})'
                layout.append([sg.Text(txt), sg.Button("❌", key=f"-DEL-{i}-")])

            layout += [
                [sg.Text("Mode entre filtres :")],
                [
                    sg.Radio("AND", "MODE", default=True, key="-MODE-AND-"),
                    sg.Radio("OR", "MODE", default=False, key="-MODE-OR-")
                ],
                [sg.Button("Appliquer"), sg.Button("Fermer")]
            ]

            return layout

        # --- Création du popup ---
        popup = sg.Window(
            f"Filtre {col_name}",
            build_layout(),
            modal=True,
            keep_on_top=True,
            finalize=True,
            disable_close=True,
            location=popup_location
        )

        changed = False
        last_position = popup_location

        # --- Boucle popup ---
        while True:
            ev_p, vals_p = popup.read()

            # Mise à jour position en live
            if ev_p == "-Configure-":
                try:
                    last_position = popup.current_location()
                except:
                    pass
                continue

            # --- Fermer sans appliquer ---
            if ev_p == "Fermer":
                popup.close()
                return False, last_position

            # --- Appliquer et fermer ---
            if ev_p == "Appliquer":
                popup.close()
                return changed, last_position

            # --- Ajouter un filtre ---
            if ev_p == "-ADD-":
                op = vals_p["-OP-"]
                val = vals_p["-VAL-"]
                mode = "AND" if vals_p["-MODE-AND-"] else "OR"

                if val:
                    self.manager.add_filter(category, col_name, val, op=op, mode=mode)
                    changed = True
                    existing_filters = self.manager.get_filters(category)[col_name]

                # On reconstruit le popup sans perdre la position
                popup.close()
                return self.open_filter_popup(parent_window, category, col_name, last_position)

            # --- Supprimer un filtre ---
            if isinstance(ev_p, str) and ev_p.startswith("-DEL-"):
                idx = int(ev_p.split("-")[2])
                self.manager.filters[category][col_name].pop(idx)
                changed = True
                existing_filters = self.manager.get_filters(category)[col_name]

                # On reconstruit le popup sans perdre la position
                popup.close()
                return self.open_filter_popup(parent_window, category, col_name, last_position)
