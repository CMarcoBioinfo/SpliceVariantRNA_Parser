import PySimpleGUI as sg

class PopupManager:
    """Mémorise la position du popup pour la réutiliser."""
    def __init__(self):
        self.last_position = None

    def get_position(self, parent_window):
        """Position d'ouverture du popup."""
        if self.last_position is not None:
            return self.last_position

        # Position centrée sur la fenêtre parent
        wx, wy = parent_window.current_location()
        ww, wh = parent_window.size
        return (wx + ww // 2, wy + wh // 2)


class FilterUI:
    """Gère l'UI des filtres : popup, opérateurs, suppression, etc."""
    def __init__(self, events_manager):
        self.manager = events_manager
        self.popup_manager = PopupManager()

    def open_filter_popup(self, parent_window, category, col_name):
        """Ouvre le popup de filtre et renvoie True si la table doit être rafraîchie."""

        existing_filters = self.manager.get_filters(category).get(col_name, [])
        ops = ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="]

        # --- Construction du layout ---
        layout_popup = [
            [sg.Text(f"Filtre pour {col_name}", font=("Arial", 12, "bold"))],
            [sg.Text("Opérateur :"), sg.Combo(ops, default_value="contains", key="-OP-")],
            [sg.Text("Valeur :"), sg.Input(key="-VAL-")],
            [sg.Button("+ Ajouter", key="-ADD-")],
            [sg.Text("Filtres actifs :")],
        ]

        for i, f in enumerate(existing_filters):
            bullet = "•" if f["mode"] == "AND" else "○"
            txt = f'{bullet} {f["op"]} "{f["value"]}" ({f["mode"]})'
            layout_popup.append([sg.Text(txt), sg.Button("❌", key=f"-DEL-{i}-")])

        layout_popup += [
            [sg.Text("Mode entre filtres :")],
            [
                sg.Radio("AND", "MODE", default=True, key="-MODE-AND-"),
                sg.Radio("OR", "MODE", default=False, key="-MODE-OR-")
            ],
            [sg.Button("Appliquer"), sg.Button("Fermer")]
        ]

        # --- Création du popup ---
        popup = sg.Window(
            f"Filtre {col_name}",
            layout_popup,
            modal=True,
            keep_on_top=True,
            finalize=True,
            disable_close=True,  # ❗ empêche la croix
            location=self.popup_manager.get_position(parent_window)
        )

        changed = False

        # --- Boucle popup ---
        while True:
            ev_p, vals_p = popup.read()

            # Capture la position quand la fenêtre bouge
            if ev_p == "-Configure-":
                try:
                    self.popup_manager.last_position = popup.current_location()
                except:
                    pass
                continue

            # --- Fermer sans appliquer ---
            if ev_p == "Fermer":
                popup.close()
                return False

            # --- Appliquer et fermer ---
            if ev_p == "Appliquer":
                popup.close()
                return changed

            # --- Ajouter un filtre (reste ouvert) ---
            if ev_p == "-ADD-":
                op = vals_p["-OP-"]
                val = vals_p["-VAL-"]
                mode = "AND" if vals_p["-MODE-AND-"] else "OR"

                if val:
                    self.manager.add_filter(category, col_name, val, op=op, mode=mode)
                    changed = True

                popup.close()
                # On rouvre pour afficher la liste mise à jour
                return self.open_filter_popup(parent_window, category, col_name)

            # --- Supprimer un filtre (reste ouvert) ---
            if isinstance(ev_p, str) and ev_p.startswith("-DEL-"):
                idx = int(ev_p.split("-")[2])
                self.manager.filters[category][col_name].pop(idx)
                changed = True

                popup.close()
                # On rouvre pour afficher la liste mise à jour
                return self.open_filter_popup(parent_window, category, col_name)

