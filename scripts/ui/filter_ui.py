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

                # Premier bloc → pas de logique
                if b_idx == 0:
                    out.append(f"[Bloc {b_idx+1}]")
                else:
                    out.append(f"[Bloc {b_idx+1} - {block['logic']}]")

                # Conditions
                for c_idx, cond in enumerate(block["conditions"]):
                    if c_idx == 0:
                        out.append(f'   • {cond["op"]} "{cond["value"]}"')
                    else:
                        out.append(f'   • ({cond["logic"]}) {cond["op"]} "{cond["value"]}"')

                out.append("")

            return out

        # ---------------------------------------------------------
        # Prévisualisation dynamique (basée sur working_copy)
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
        # Filtre actif (basé sur manager, pas working_copy)
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

            [sg.Text("Opérateur logique :"),
             sg.Radio("AND", "CONDLOG", default=True, key="-COND-AND-"),
             sg.Radio("OR", "CONDLOG", default=False, key="-COND-OR-")],

            [sg.Button("+ Ajouter condition", key="-ADD-COND-"),
             sg.Button("+ Ajouter bloc", key="-ADD-BLOCK-")],

            # Prévisualisation scrollable
            [sg.Frame("Prévisualisation du filtre", [
                [sg.Multiline(
                    "",
                    key="-PREVIEW-",
                    size=(80, 6),
                    disabled=True,
                    autoscroll=False,
                    no_scrollbar=False,
                    horizontal_scroll=False,
                    auto_size_text=False
                )]
            ], relief=sg.RELIEF_SUNKEN)],

            # Filtre actif scrollable
            [sg.Frame("Filtre actif (appliqué)", [
                [sg.Multiline(
                    "",
                    key="-ACTIVE-",
                    size=(80, 5),
                    disabled=True,
                    autoscroll=False,
                    no_scrollbar=False,
                    horizontal_scroll=False,
                    auto_size_text=False
                )]
            ], relief=sg.RELIEF_SUNKEN)],

            [sg.Text("Filtres détaillés :")],
            [sg.Listbox(values=format_blocks(), key="-LIST-", size=(80,12), enable_events=True)],

            [sg.Button("Supprimer", key="-DEL-"),
             sg.Button("Changer logique", key="-TOGGLE-LOGIC-"),
             sg.Button("Effacer tout", key="-CLEAR-")],

            [
                sg.Frame(
                    "Filter :",
                    [
                        [sg.Button("Enregistrer", key="-SAVE-FILTER-", size=(15,1))],
                        [sg.Button("Charger", key="-LOAD-FILTER-", size=(15,1))]
                    ],
                    relief=sg.RELIEF_GROOVE,
                    element_justification="center",
                    vertical_alignment="top",
                    pad=((0,0),(10,10))
                )
            ],

            [sg.Button("Appliquer"), sg.Button("Fermer")]
        ]

        # ---------------------------------------------------------
        # Création de la popup
        # ---------------------------------------------------------

        if saved_position:
            # Ouvrir directement à la position sauvegardée
            popup = sg.Window(
                f"Filtre {col_name}",
                layout,
                modal=True,
                keep_on_top=True,
                finalize=True,
                disable_close=True,
                location=saved_position
            )
            last_position = saved_position

        else:
            # 1) Ouvrir hors écran pour mesurer
            popup = sg.Window(
                f"Filtre {col_name}",
                layout,
                modal=True,
                keep_on_top=True,
                finalize=True,
                disable_close=True,
                location=(-10000, -10000)
            )

            # 2) Taille réelle de la popup
            pw, ph = popup.size

            # 3) Taille et position du parent
            wx, wy = parent_window.current_location()
            ww, wh = parent_window.size

            # 4) Calcul du centrage
            px = wx + (ww - pw) // 2
            py = wy + (wh - ph) // 2

            # 5) Déplacer la popup au centre
            popup.move(px, py)

            last_position = (px, py)

        # Mise à jour initiale
        popup["-PREVIEW-"].update(format_preview())
        popup["-ACTIVE-"].update(format_active())

        changed = False

        selected_block = None
        selected_condition = None

        # ---------------------------------------------------------
        # Boucle popup
        # ---------------------------------------------------------
        while True:
            ev, vals = popup.read()

            # Sauvegarde position si la fenêtre est déplacée
            try:
                last_position = popup.current_location()
            except:
                pass

            # Fermer → ne rien appliquer
            if ev in (sg.WIN_CLOSED, "Fermer"):
                popup.close()
                return False, last_position

            # Appliquer → on copie working_copy dans manager
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

            # Sélection dans la Listbox
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

            # Ajouter un bloc
            if ev == "-ADD-BLOCK-":
                logic = "AND" if vals["-COND-AND-"] else "OR"
                working_copy.append({"logic": logic, "conditions": []})
                changed = True

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # Ajouter une condition
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

                    changed = True

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # Supprimer
            if ev == "-DEL-":
                if selected_block is not None and selected_condition is not None:
                    del working_copy[selected_block]["conditions"][selected_condition]
                    changed = True

                elif selected_block is not None:
                    del working_copy[selected_block]
                    changed = True

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # Effacer tout
            if ev == "-CLEAR-":
                working_copy = []
                popup["-LIST-"].update(values=[])
                popup["-PREVIEW-"].update("Aucun filtre")
                changed = True

            # Changer logique
            if ev == "-TOGGLE-LOGIC-":

                if selected_block is not None and selected_condition is not None:
                    if selected_condition != 0:
                        cond = working_copy[selected_block]["conditions"][selected_condition]
                        cond["logic"] = "OR" if cond["logic"] == "AND" else "AND"
                        changed = True

                elif selected_block is not None and selected_block != 0:
                    block = working_copy[selected_block]
                    block["logic"] = "OR" if block["logic"] == "AND" else "AND"
                    changed = True

                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())

            # ---------------------------------------------------------
            # ENREGISTRER FILTRE
            # ---------------------------------------------------------
            if ev == "-SAVE-FILTER-":
                name = sg.popup_get_text("Nom du filtre :", default_text="")
                if not name:
                    continue
            
                scope = sg.popup_yes_no("Enregistrer comme filtre PERSONNEL ?\n"
                                        "(Non = filtre GLOBAL)")
                scope = "personal" if scope == "Yes" else "global"
            
                # Nettoyage des blocs vides
                cleaned = [b for b in working_copy if len(b["conditions"]) > 0]
            
                self.storage.save_column_filter(
                    column=col_name,
                    name=name,
                    blocks=cleaned,
                    scope=scope
                )
            
                sg.popup_ok("Filtre enregistré.")


            # ---------------------------------------------------------
            # CHARGER FILTRE
            # ---------------------------------------------------------
            if ev == "-LOAD-FILTER-":
            
                scope = sg.popup_yes_no("Charger un filtre PERSONNEL ?\n"
                                        "(Non = filtre GLOBAL)")
                scope = "personal" if scope == "Yes" else "global"
            
                names = self.storage.list_filters(
                    scope=scope,
                    filter_type="column",
                    column=col_name
                )
            
                if not names:
                    sg.popup_ok("Aucun filtre trouvé.")
                    continue
            
                name = sg.popup_get_text(
                    "Nom du filtre à charger :\n" + "\n".join(names)
                )
                if not name:
                    continue
            
                loaded = self.storage.load_column_filter(name, scope)
                if not loaded:
                    sg.popup_ok("Erreur : filtre introuvable.")
                    continue
            
                _, blocks = loaded
                working_copy = copy.deepcopy(blocks)
            
                popup["-LIST-"].update(values=format_blocks())
                popup["-PREVIEW-"].update(format_preview())


