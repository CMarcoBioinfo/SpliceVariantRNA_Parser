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

                # Premier bloc → pas de logique
                if b_idx == 0:
                    out.append(f"[Bloc {b_idx+1}]")
                else:
                    out.append(f"[Bloc {b_idx+1} — logique: {block['logic']}]")

                # Conditions
                for c_idx, cond in enumerate(block["conditions"]):
                    if c_idx == 0:
                        out.append(f'   • {cond["op"]} "{cond["value"]}"')
                    else:
                        out.append(f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"')

                out.append("")

            return out

        # ---------------------------------------------------------
        # Formatage du filtre actif (résumé lisible)
        # ---------------------------------------------------------
        def format_filter_expression():
            blocks = self.manager.get_filters(category).get(col_name, [])
            if not blocks:
                return "Aucun filtre actif"

            parts = []

            for b_idx, block in enumerate(blocks):
                conds = block["conditions"]
                if not conds:
                    continue

                cond_parts = []
                for c_idx, cond in enumerate(conds):
                    if c_idx == 0:
                        cond_parts.append(f'{cond["op"]} "{cond["value"]}"')
                    else:
                        cond_parts.append(f'{cond["logic"]} {cond["op"]} "{cond["value"]}"')

                block_expr = "(" + " ".join(cond_parts) + ")"

                if b_idx == 0:
                    parts.append(block_expr)
                else:
                    parts.append(f'{block["logic"]} {block_expr}')

            return " ".join(parts)

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

            [sg.Text("Filtre actif :")],
            [sg.Text("", key="-ACTIVE-")],

            [sg.Text("Filtres détaillés :")],
            [sg.Listbox(values=format_blocks(), key="-LIST-", size=(50,12), enable_events=True)],

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

        popup["-ACTIVE-"].update(format_filter_expression())

        changed = False
        last_position = popup_location

        selected_block = None
        selected_condition = None

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

            # Sélection dans la Listbox
            if ev == "-LIST-":
                selected = vals["-LIST-"]
                selected_block = None
                selected_condition = None

                if selected:
                    line = selected[0]
                    blocks = self.manager.get_filters(category).get(col_name, [])

                    # Bloc ?
                    for b_idx, block in enumerate(blocks):
                        if f"[Bloc {b_idx+1}" in line:
                            selected_block = b_idx
                            break

                    # Condition ?
                    if selected_block is None:
                        for b_idx, block in enumerate(blocks):
                            for c_idx, cond in enumerate(block["conditions"]):
                                txt1 = f'   • {cond["op"]} "{cond["value"]}"'
                                txt2 = f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"'
                                if line == txt1 or line == txt2:
                                    selected_block = b_idx
                                    selected_condition = c_idx
                                    break

            # Ajouter un bloc
            if ev == "-ADD-BLOCK-":
                self.manager.add_block(category, col_name)
                popup["-LIST-"].update(values=format_blocks())
                popup["-ACTIVE-"].update(format_filter_expression())
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
                        blocks = self.manager.get_filters(category).get(col_name, [])

                    # Ajouter dans le bloc sélectionné
                    if selected_block is not None:
                        b_idx = selected_block
                    else:
                        b_idx = len(blocks) - 1

                    # Première condition → pas de logique
                    if len(blocks[b_idx]["conditions"]) == 0:
                        logic = None

                    self.manager.add_condition(category, col_name, b_idx, op, val, logic)
                    changed = True

                popup["-LIST-"].update(values=format_blocks())
                popup["-ACTIVE-"].update(format_filter_expression())

            # Supprimer une condition
            if ev == "-DEL-":
                if selected_block is not None and selected_condition is not None:
                    self.manager.remove_condition(category, col_name, selected_block, selected_condition)
                    changed = True
                    popup["-LIST-"].update(values=format_blocks())
                    popup["-ACTIVE-"].update(format_filter_expression())

            # Changer logique du bloc
            if ev == "-TOGGLE-BLOCK-":
                if selected_block is not None and selected_block != 0:
                    blocks = self.manager.get_filters(category).get(col_name, [])
                    block = blocks[selected_block]
                    block["logic"] = "OR" if block["logic"] == "AND" else "AND"
                    changed = True
                    popup["-LIST-"].update(values=format_blocks())
                    popup["-ACTIVE-"].update(format_filter_expression())

