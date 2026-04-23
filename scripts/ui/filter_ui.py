import PySimpleGUI as sg

class FilterUI:
    def __init__(self, manager):
        self.manager = manager

    def open_filter_popup(self, parent_window, category, col_name, saved_position=None):

        # --- Position d'ouverture ---
        if saved_position:
            popup_location = saved_position
        else:
            wx, wy = parent_window.current_location()
            ww, wh = parent_window.size
            popup_location = (wx + ww // 2, wy + wh // 2)

        # ---------------------------------------------------------
        # FORMATAGE TEXTE (stable, comme l’ancienne version)
        # ---------------------------------------------------------
        def format_groups():
            out = []
            groups = self.manager.get_filters(category).get(col_name, [])

            for g_idx, group in enumerate(groups):
                out.append(f"[Groupe {g_idx+1} — OR]")

                for cond in group["conditions"]:
                    out.append(f'   • {cond["op"]} "{cond["value"]}"')

                out.append("")  # ligne vide

            return out

        # ---------------------------------------------------------
        # LAYOUT PRINCIPAL (statique = stable)
        # ---------------------------------------------------------
        layout = [
            [sg.Text(f"Filtres pour {col_name}", font=("Arial", 12, "bold"))],

            [sg.Text("Opérateur :"),
             sg.Combo(["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="],
                      default_value="contains", key="-OP-", size=(12,1))],

            [sg.Text("Valeur :"), sg.Input(key="-VAL-", size=(20,1))],

            [sg.Button("+ Ajouter OR", key="-ADD-OR-"),
             sg.Button("+ Ajouter groupe AND", key="-ADD-GROUP-")],

            [sg.Text("Filtres actifs :")],
            [sg.Listbox(values=format_groups(), key="-LIST-", size=(45,12))],

            [sg.Button("Supprimer", key="-DEL-")],
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
            resizable=False
        )

        changed = False
        last_position = popup_location

        # ---------------------------------------------------------
        # BOUCLE POPUP
        # ---------------------------------------------------------
        while True:
            ev, vals = popup.read()

            # Sauvegarde position
            if popup.TKroot:
                try:
                    last_position = popup.current_location()
                except:
                    pass

            if ev in (sg.WIN_CLOSED, "Fermer"):
                popup.close()
                return False, last_position

            if ev == "Appliquer":
                popup.close()
                return changed, last_position

            # Ajouter un groupe AND
            if ev == "-ADD-GROUP-":
                self.manager.add_filter_group(category, col_name)
                popup["-LIST-"].update(values=format_groups())
                changed = True

            # Ajouter une condition OR
            if ev == "-ADD-OR-":
                op = vals["-OP-"]
                val = vals["-VAL-"]

                if val:
                    # Ajout dans le dernier groupe
                    groups = self.manager.get_filters(category).get(col_name, [])
                    if not groups:
                        self.manager.add_filter_group(category, col_name)

                    g_idx = len(groups) - 1
                    self.manager.add_condition(category, col_name, g_idx, op, val)
                    changed = True

                popup["-LIST-"].update(values=format_groups())

            # Supprimer
            if ev == "-DEL-":
                selected = vals["-LIST-"]
                if not selected:
                    continue

                line = selected[0]

                # Trouver groupe + condition
                groups = self.manager.get_filters(category).get(col_name, [])
                idx = 0
                for g_idx, group in enumerate(groups):
                    for c_idx, cond in enumerate(group["conditions"]):
                        text = f'   • {cond["op"]} "{cond["value"]}"'
                        if text == line:
                            self.manager.remove_condition(category, col_name, g_idx, c_idx)
                            changed = True
                            popup["-LIST-"].update(values=format_groups())
                            break

        # fin boucle


