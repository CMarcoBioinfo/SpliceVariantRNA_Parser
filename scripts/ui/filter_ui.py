import PySimpleGUI as sg
import copy

class FilterUI:
    def __init__(self, manager, storage):
        self.manager = manager
        self.storage = storage

    def open_filter_popup(self, parent_window, category, col_name, saved_position=None):

        # ---------------------------------------------------------
        # COPIE DE TRAVAIL (working_copy)
        # ---------------------------------------------------------
        working_copy = copy.deepcopy(
            self.manager.get_filters(category).get(col_name, [])
        )

        # ---------------------------------------------------------
        # Formatage texte pour la Listbox
        # ---------------------------------------------------------
        def format_blocks():
            out = []
            blocks = working_copy

            for b_idx, block in enumerate(blocks):

                if b_idx == 0:
                    out.append(f"[Bloc {b_idx+1}]")
                else:
                    out.append(f"[Bloc {b_idx+1} - {block['logic']}]")

                for c_idx, cond in enumerate(block["conditions"]):
                    if c_idx == 0:
                        out.append(f'   • {cond["op"]} "{cond["value"]}"')
                    else:
                        out.append(f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"')

                out.append("")

            return out

        # ---------------------------------------------------------
        # Prévisualisation dynamique
        # ---------------------------------------------------------
        def format_preview():
            blocks = working_copy
            if not blocks:
                return "Aucun filtre"

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
        # Filtre actif
        # ---------------------------------------------------------
        def format_active():
            blocks = self.manager.get_filters(category).get(col_name, [])
            if not blocks:
                return "Aucun filtre appliqué"

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
        # Layout principal (inchangé)
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

            [sg.Text("Opérateur logique :"),
             sg.Radio("AND", "CONDLOG", default=True, key="-COND-AND-"),
             sg.Radio("OR", "CONDLOG", default=False, key="-COND-OR-")],

            [sg.Button("+ Ajouter condition", key="-ADD-COND-"),
             sg.Button("+ Ajouter bloc", key="-ADD-BLOCK-")],

            [sg.Frame("Prévisualisation du filtre", [
                [sg.Multiline("", key="-PREVIEW-", size=(80, 6), disabled=True)]
            ], relief=sg.RELIEF_SUNKEN)],

            [sg.Frame("Filtre actif (appliqué)", [
                [sg.Multiline("", key="-ACTIVE-", size=(80, 5), disabled=True)]
            ], relief=sg.RELIEF_SUNKEN)],

            [sg.Text("Filtres détaillés :")],
            [sg.Listbox(values=format_blocks(), key="-LIST-", size=(80,12), enable_events=True)],

            # Actions du filtre
            [
                sg.Frame(
                    "Actions du filtre",
                    [
                        [
                            sg.Button("Supprimer", key="-DEL-", size=(12,1)),
                            sg.Button("Changer logique", key="-TOGGLE-LOGIC-", size=(14,1)),
                            sg.Button("Effacer tout", key="-CLEAR-", size=(12,1))
                        ]
                    ],
                    relief=sg.RELIEF_GROOVE,
                    pad=((0,0),(10,10))
                )
            ],

            # Gestion des filtres (inchangé sauf ajout bouton supprimer)
            [
                sg.Frame(
                    "Gestion des filtres",
                    [
                        [
                            sg.Button("Enregistrer", key="-SAVE-FILTER-", size=(12,1)),
                            sg.Button("Charger", key="-LOAD-FILTER-", size=(12,1)),
                            sg.Button("Supprimer filtre", key="-DELETE-FILTER-", size=(15,1))
                        ]
                    ],
                    relief=sg.RELIEF_GROOVE,
                    pad=((0,0),(10,10))
                )
            ],

            [
                sg.Button("Appliquer", size=(12,1)),
                sg.Push(),
                sg.Button("Fermer", size=(12,1))
            ]
        ]

        # ---------------------------------------------------------
        # Création popup centré (version fiable)
        # ---------------------------------------------------------
        popup = sg.Window(
            f"Filtre {col_name}",
            layout,
            modal=True,
            keep_on_top=True,
            finalize=True,
            disable_close=True,
            location=(-10000, -10000)
        )

        popup.TKroot.update_idletasks()
        pw = popup.TKroot.winfo_width()
        ph = popup.TKroot.winfo_height()

        wx, wy = parent_window.current_location()
        ww, wh = parent_window.size

        px = wx + (ww - pw) // 2
        py = wy + (wh - ph) // 2

        popup.move(px, py)
        last_position = (px, py)

        popup["-PREVIEW-"].update(format_preview())
        popup["-ACTIVE-"].update(format_active())

        selected_block = None
        selected_condition = None

        # ---------------------------------------------------------
        # Boucle popup
        # ---------------------------------------------------------
        while True:
            ev, vals = popup.read()

            try:
                last_position = popup.current_location()
            except:
                pass

            if ev in (sg.WIN_CLOSED, "Fermer"):
                popup.close()
                return False, last_position

            if ev == "Appliquer":
                cleaned = [b for b in working_copy if len(b["conditions"]) > 0]

                if cleaned:
                    if category not in self.manager.filters:
                        self.manager.filters[category] = {}
                    self.manager.filters[category][col_name] = cleaned
                else:
                    if col_name in self.manager.filters.get(category, {}):
                        del self.manager.filters[category][col_name]

                popup.close()
                return True, last_position

            # ---------------------------------------------------------
            # Sélection listbox
            # ---------------------------------------------------------
            if ev == "-LIST-":
                selected = vals["-LIST-"]
                selected_block = None
                selected_condition = None

                if selected:
                    line = selected[0]

                    for b_idx, block in enumerate(working_copy):
                        if f"[Bloc {b_idx+1}" in line:
                            selected_block = b_idx
                            break

                    if selected_block is None:
                        for b_idx, block in enumerate(working_copy):
                            for c_idx, cond in enumerate(block["conditions"]):
                                txt1 = f'   • {cond["op"]} "{cond["value"]}"'
                                txt2 = f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"'
                                if line == txt1 or line == txt2:
                                    selected_block = b_idx
                                    selected_condition = c_idx
                                    break

            # ---------------------------------------------------------
            # Ajouter bloc
            # ---------------------------------------------------------
            if ev == "-ADD-BLOCK-":
                logic = "AND" if vals["-COND-AND-"] else "OR"
                working_copy.append({"logic": logic, "conditions": []})

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # ---------------------------------------------------------
            # Ajouter condition
            # ---------------------------------------------------------
            if ev == "-ADD-COND-":
                op = vals["-OP-"]
                val = vals["-VAL-"]
                logic = "AND" if vals["-COND-AND-"] else "OR"

                if val:

                    if not working_copy:
                        working_copy.append({"logic": "AND", "conditions": []})

                    if selected_block is not None:
                        b_idx = selected_block
                    else:
                        b_idx = len(working_copy) - 1

                    if len(working_copy[b_idx]["conditions"]) == 0:
                        logic = None

                    working_copy[b_idx]["conditions"].append({
                        "op": op,
                        "value": val,
                        "logic": logic
                    })

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # ---------------------------------------------------------
            # Supprimer condition ou bloc
            # ---------------------------------------------------------
            if ev == "-DEL-":
                if selected_block is not None and selected_condition is not None:
                    del working_copy[selected_block]["conditions"][selected_condition]

                elif selected_block is not None:
                    del working_copy[selected_block]

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # ---------------------------------------------------------
            # Effacer tout
            # ---------------------------------------------------------
            if ev == "-CLEAR-":
                working_copy = []
                popup["-LIST-"].update(values=[])
                popup["-PREVIEW-"].update("Aucun filtre")

            # ---------------------------------------------------------
            # Changer logique
            # ---------------------------------------------------------
            if ev == "-TOGGLE-LOGIC-":

                if selected_block is not None and selected_condition is not None:
                    if selected_condition != 0:
                        cond = working_copy[selected_block]["conditions"][selected_condition]
                        cond["logic"] = "OR" if cond["logic"] == "AND" else "AND"

                elif selected_block is not None and selected_block != 0:
                    block = working_copy[selected_block]
                    block["logic"] = "OR" if block["logic"] == "AND" else "AND"

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # ---------------------------------------------------------
            # ENREGISTRER FILTRE
            # ---------------------------------------------------------
            if ev == "-SAVE-FILTER-":

                layout_save = [
                    [sg.Text("Nom du filtre :")],
                    [sg.Input(key="-SAVE-NAME-")],

                    [sg.Text("Scope :")],
                    [
                        sg.Radio("Personnel", "SCOPE_SAVE", key="-SAVE-PERSO-", default=True),
                        sg.Radio("Global", "SCOPE_SAVE", key="-SAVE-GLOBAL-")
                    ],

                    [sg.Push(), sg.Button("OK"), sg.Button("Annuler")]
                ]

                win = sg.Window("Enregistrer filtre", layout_save, modal=True, keep_on_top=True)

                while True:
                    ev2, vals2 = win.read()
                    if ev2 in (sg.WIN_CLOSED, "Annuler"):
                        win.close()
                        break

                    if ev2 == "OK":
                        name = vals2["-SAVE-NAME-"]
                        if not name:
                            sg.popup_ok("Nom invalide.")
                            continue

                        scope = "personal" if vals2["-SAVE-PERSO-"] else "global"

                        cleaned = [b for b in working_copy if len(b["conditions"]) > 0]

                        self.storage.save_column_filter(
                            column=col_name,
                            name=name,
                            blocks=cleaned,
                            scope=scope
                        )

                        win.close()
                        sg.popup_ok("Filtre enregistré.")
                        break

            # ---------------------------------------------------------
            # CHARGER FILTRE
            # ---------------------------------------------------------
            if ev == "-LOAD-FILTER-":

                layout_scope = [
                    [sg.Text("Charger un filtre :")],
                    [
                        sg.Radio("Personnel", "SCOPE_LOAD", key="-LOAD-PERSO-", default=True),
                        sg.Radio("Global", "SCOPE_LOAD", key="-LOAD-GLOBAL-")
                    ],
                    [sg.Button("Suivant"), sg.Button("Annuler")]
                ]

                win1 = sg.Window("Choisir scope", layout_scope, modal=True, keep_on_top=True)
                ev2, vals2 = win1.read()
                if ev2 in (sg.WIN_CLOSED, "Annuler"):
                    win1.close()
                    continue

                scope = "personal" if vals2["-LOAD-PERSO-"] else "global"
                win1.close()

                names = self.storage.list_filters(
                    scope=scope,
                    filter_type="column",
                    column=col_name
                )

                if not names:
                    sg.popup_ok("Aucun filtre trouvé.")
                    continue

                layout_load = [
                    [sg.Text("Sélectionner un filtre :")],
                    [sg.Combo(names, key="-LOAD-NAME-", readonly=True, size=(25,1))],
                    [sg.Push(), sg.Button("Charger"), sg.Button("Annuler")]
                ]

                win2 = sg.Window("Charger filtre", layout_load, modal=True, keep_on_top=True)

                while True:
                    ev3, vals3 = win2.read()
                    if ev3 in (sg.WIN_CLOSED, "Annuler"):
                        win2.close()
                        break

                    if ev3 == "Charger":
                        name = vals3["-LOAD-NAME-"]
                        if not name:
                            sg.popup_ok("Aucun filtre sélectionné.")
                            continue

                        loaded = self.storage.load_column_filter(name, scope)
                        if not loaded:
                            sg.popup_ok("Erreur : filtre introuvable.")
                            continue

                        _, blocks = loaded
                        working_copy = copy.deepcopy(blocks)

                        popup["-LIST-"].update(values=format_blocks())
                        popup["-PREVIEW-"].update(format_preview())

                        win2.close()
                        break

            # ---------------------------------------------------------
            # SUPPRIMER FILTRE
            # ---------------------------------------------------------
            if ev == "-DELETE-FILTER-":

                layout_scope = [
                    [sg.Text("Supprimer un filtre :")],
                    [
                        sg.Radio("Personnel", "SCOPE_DEL", key="-DEL-PERSO-", default=True),
                        sg.Radio("Global", "SCOPE_DEL", key="-DEL-GLOBAL-")
                    ],
                    [sg.Button("Suivant"), sg.Button("Annuler")]
                ]

                win1 = sg.Window("Choisir scope", layout_scope, modal=True, keep_on_top=True)
                ev2, vals2 = win1.read()
                if ev2 in (sg.WIN_CLOSED, "Annuler"):
                    win1.close()
                    continue

                scope = "personal" if vals2["-DEL-PERSO-"] else "global"
                win1.close()

                names = self.storage.list_filters(
                    scope=scope,
                    filter_type="column",
                    column=col_name
                )

                if not names:
                    sg.popup_ok("Aucun filtre à supprimer.")
                    continue

                layout_del = [
                    [sg.Text("Sélectionner un filtre à supprimer :")],
                    [sg.Combo(names, key="-DEL-NAME-", readonly=True, size=(25,1))],
                    [sg.Push(), sg.Button("Supprimer"), sg.Button("Annuler")]
                ]

                win2 = sg.Window("Supprimer filtre", layout_del, modal=True, keep_on_top=True)

                while True:
                    ev3, vals3 = win2.read()
                    if ev3 in (sg.WIN_CLOSED, "Annuler"):
                        win2.close()
                        break

                    if ev3 == "Supprimer":
                        name = vals3["-DEL-NAME-"]
                        if not name:
                            sg.popup_ok("Aucun filtre sélectionné.")
                            continue

                        ok = self.storage.delete_column_filter(name, scope)

                        if ok:
                            sg.popup_ok("Filtre supprimé.")
                        else:
                            sg.popup_ok("Erreur : impossible de supprimer.")

                        win2.close()
                        break
