import PySimpleGUI as sg

class FilterUI:
    def __init__(self, manager):
        self.manager = manager

    def open_filter_popup(self, parent_window, category, col_name, saved_position=None):

        # ---------------------------------------------------------
        # Position d’ouverture
        # ---------------------------------------------------------
        if saved_position:
            popup_location = saved_position
        else:
            wx, wy = parent_window.current_location()
            ww, wh = parent_window.size
            popup_location = (wx + ww // 2, wy + wh // 2)

        # ---------------------------------------------------------
        # Formatage texte pour la Listbox
        # ---------------------------------------------------------
        def format_blocks():
            out = []
            blocks = self.manager.get_filters(category).get(col_name, [])

            for b_idx, block in enumerate(blocks):
                out.append(f"[Bloc {b_idx+1} — logique: {block['logic']}]")

                for cond in block["conditions"]:
                    out.append(f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"')

                out.append("")  # ligne vide

            return out

        # ---------------------------------------------------------
        # Layout principal
        # ---------------------------------------------------------
        layout = [
            [sg.Text(f"Filtres pour {col_name}", font=("Arial", 12, "bold"))],

            [sg.Text("Opérateur :"),
             sg.Combo(
                 ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="],
                 default_value="contains",
                 key="-OP-",
                 size=(12,1)
             )],

            [sg.Text("Valeur :"), sg.Input(key="-VAL-", size=(20,1))],

            [sg.Text("Logique avec la suivante :"),
             sg.Radio("AND", "CONDLOG", default=True, key="-COND-AND-"),
             sg.Radio("OR", "CONDLOG", default=False, key="-COND-OR-")],

            [sg.Button("+ Ajouter condition", key="-ADD-COND-"),
             sg.Button("+ Ajouter bloc", key="-ADD-BLOCK-")],

            [sg.Text("Filtres actifs :")],
            [sg.Listbox(values=format_blocks(), key="-LIST-", size=(50,12))],

            [sg.Button("Supprimer", key="-DEL-"),
             sg.Button("Changer logique du bloc", key="-TOGGLE-BLOCK-")],

            [sg.Button("Appliquer"), sg.Button("Fermer")]
        ]

        popup = sg.Window(
            f"Filtre {col_name}",
            layout,
            modal=True,
            keep_on_top=True,
            finalize=True,
            disable_close=True,
            location=popup_location
        )

        changed = False
        last_position = popup_location

        # ---------------------------------------------------------
        # Boucle popup
        # ---------------------------------------------------------
        while True:
            ev, vals = popup.read()

            # Sauvegarde position
            if popup.TKroot:
                try:
                    last_position = popup.current_location()
                except:
                    pass

            # Fermer
            if ev in (sg.WIN_CLOSED, "Fermer"):
                popup.close()
                return False, last_position

            # Appliquer
            if ev == "Appliquer":
                popup.close()
                return changed, last_position

            # Ajouter un bloc
            if ev == "-ADD-BLOCK-":
                self.manager.add_block(category, col_name)
                popup["-LIST-"].update(values=format_blocks())
                changed = True

            # Ajouter une condition
            if ev == "-ADD-COND-":
                op = vals["-OP-"]
                val = vals["-VAL-"]
                logic = "AND" if vals["-COND-AND-"] else "OR"

                if val:
                    blocks = self.manager.get_filters(category).get(col_name, [])
                    if not blocks:
                        self.manager.add_block(category, col_name)

                    b_idx = len(blocks) - 1
                    self.manager.add_condition(category, col_name, b_idx, op, val, logic)
                    changed = True

                popup["-LIST-"].update(values=format_blocks())

            # Supprimer une condition
            if ev == "-DEL-":
                selected = vals["-LIST-"]
                if not selected:
                    continue

                line = selected[0]
                blocks = self.manager.get_filters(category).get(col_name, [])

                for b_idx, block in enumerate(blocks):
                    for c_idx, cond in enumerate(block["conditions"]):
                        text = f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"'
                        if text == line:
                            self.manager.remove_condition(category, col_name, b_idx, c_idx)
                            changed = True
                            popup["-LIST-"].update(values=format_blocks())
                            break

            # Changer logique du bloc (AND <-> OR)
            if ev == "-TOGGLE-BLOCK-":
                selected = vals["-LIST-"]
                if not selected:
                    continue

                line = selected[0]
                blocks = self.manager.get_filters(category).get(col_name, [])

                for b_idx, block in enumerate(blocks):
                    if f"[Bloc {b_idx+1}" in line:
                        block["logic"] = "OR" if block["logic"] == "AND" else "AND"
                        changed = True
                        popup["-LIST-"].update(values=format_blocks())
                        break
