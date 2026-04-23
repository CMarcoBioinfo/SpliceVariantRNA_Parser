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
        # RECONSTRUCTION DU LAYOUT DYNAMIQUE
        # ---------------------------------------------------------
        def build_filters_layout():
            layout = []
            filters = self.manager.get_filters(category).get(col_name, [])

            for g_idx, group in enumerate(filters):
                layout.append([sg.Text(f"Groupe {g_idx+1} (OR)", font=("Arial", 11, "bold"))])

                # Conditions existantes
                for c_idx, cond in enumerate(group["conditions"]):
                    layout.append([
                        sg.Combo(
                            ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="],
                            default_value=cond["op"],
                            key=f"-OP-{g_idx}-{c_idx}-",
                            size=(10,1)
                        ),
                        sg.Input(cond["value"], key=f"-VAL-{g_idx}-{c_idx}-", size=(20,1)),
                        sg.Button("❌", key=f"-DEL-COND-{g_idx}-{c_idx}-")
                    ])

                # Zone de saisie pour une nouvelle condition OR
                layout.append([
                    sg.Combo(
                        ["contains", "startswith", "endswith", "=", "!=", ">", "<", ">=", "<="],
                        default_value="contains",
                        key=f"-NEW-OP-{g_idx}-",
                        size=(10,1)
                    ),
                    sg.Input("", key=f"-NEW-VAL-{g_idx}-", size=(20,1)),
                    sg.Button("+ Ajouter OR", key=f"-ADD-OR-{g_idx}-")
                ])

                layout.append([sg.HorizontalSeparator()])

            # Ajouter un groupe AND
            layout.append([sg.Button("+ Ajouter un groupe AND", key="-ADD-GROUP-")])

            return layout

        # ---------------------------------------------------------
        # LAYOUT PRINCIPAL
        # ---------------------------------------------------------
        layout = [
            [sg.Text(f"Filtres pour {col_name}", font=("Arial", 12, "bold"))],
            [sg.Column(
                build_filters_layout(),
                key="-FILTERS-COL-",
                scrollable=True,
                vertical_scroll_only=True,
                size=(450, 300)
            )],
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
            resizable=True
        )

        last_position = popup_location
        changed = False

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
                popup["-FILTERS-COL-"].update(build_filters_layout())
                changed = True

            # Ajouter une condition OR
            if ev.startswith("-ADD-OR-"):
                g_idx = int(ev.split("-")[3])
                op = vals.get(f"-NEW-OP-{g_idx}-")
                val = vals.get(f"-NEW-VAL-{g_idx}-")

                if val:
                    self.manager.add_condition(category, col_name, g_idx, op, val)
                    changed = True

                popup["-FILTERS-COL-"].update(build_filters_layout())

            # Supprimer une condition
            if ev.startswith("-DEL-COND-"):
                _, _, g_idx, c_idx, _ = ev.split("-")
                g_idx = int(g_idx)
                c_idx = int(c_idx)

                self.manager.remove_condition(category, col_name, g_idx, c_idx)
                popup["-FILTERS-COL-"].update(build_filters_layout())
                changed = True

