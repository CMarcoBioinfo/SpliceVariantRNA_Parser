import PySimpleGUI as sg
from scripts.core.qc_manager import open_qc_html
from scripts.core.sashimi_manager import open_sashimi_plot
from scripts.core.utils import is_number, parse_position


def open_patient_window(result, saved_size=None, saved_location=None):
    """
    Fenêtre d'affichage des événements RNA pour un patient.
    """

    sg.theme("SystemDefault")

    # --- Données backend ---
    patient_id = result.patient_id
    events_by_cat = result.events_by_category
    columns_by_cat = result.columns_by_category
    qc_zip = result.qc_zip
    sashimi_zip = result.sashimi_zip
    tmp_dir = result.tmp_dir
    sort_states = {}

    # --- Construction des onglets (avec tableaux dedans) ---
    tabs = []
    for cat_name, events in events_by_cat.items():
        cols = columns_by_cat.get(cat_name, [])

        table = sg.Table(
            values=[[ev.get(col + "_fmt", ev.get(col, "")) for col in cols] for ev in events],
            headings=cols,
            key=f"-TABLE-{cat_name}-",
            auto_size_columns=True,
            enable_events=True,
            enable_click_events=True,
            expand_x=True,
            expand_y=True,
            num_rows=15
        )

        tabs.append(
            sg.Tab(cat_name, [[table]], key=f"-TAB-{cat_name}-")
        )

    tab_group = sg.TabGroup(
        [tabs],
        key="-TABGROUP-",
        expand_x=True,
        expand_y=True,
        enable_events=True
    )

    # --- Layout TRGT-like ---
    layout = [
        [tab_group],

        [sg.Column([
            # --- DÉTAILS ---
            [sg.Frame(
                f"Détails {patient_id}",
                [[sg.Multiline(
                    "",
                    key="-DETAILS-",
                    disabled=True,
                    expand_x=True,
                    expand_y=True
                )]],
                expand_x=True,
                expand_y=True
            )],

            # --- BOUTONS ---
            [sg.Column([
                [
                    sg.Button("FASTQ Raw QC", key="-QC-RAW-"),
                    sg.Button("FASTQ Trimmed QC", key="-QC-TRIM-"),
                    sg.Button("BAM QC", key="-QC-BAM-"),
                    sg.Button("Sashimi Plot", key="-SASHIMI-", disabled=(sashimi_zip is None)),
                    sg.Button("Fermer", key="-CLOSE-"),
                ]
            ], expand_x=True)]
        ],
        expand_x=True,
        expand_y=True)],

        [sg.Text("", key="-STATUS-", text_color="blue")]
    ]

    # --- Création fenêtre ---
    if saved_size is None:
        window = sg.Window(
            f"SpliceVariantRNA Viewer — {patient_id}",
            layout,
            resizable=True,
            finalize=True,
            enable_close_attempted_event=True
        )
        window.maximize()
    else:
        window = sg.Window(
            f"SpliceVariantRNA Viewer — {patient_id}",
            layout,
            resizable=True,
            finalize=True,
            size=saved_size,
            location=saved_location,
            enable_close_attempted_event=True
        )

    # --- Catégorie active ---
    current_category = list(events_by_cat.keys())[0] if events_by_cat else None

    # --- Boucle événements ---
    while True:
        event, values = window.read()
        print("EVENT =", event)
        print("TYPE =",type(event))
        print("VALUES =", values)
        print("-----------------------------------------------------------------------------")

        # Sauvegarde taille/position
        if window.TKroot is not None:
            try:
                saved_size = window.size
                saved_location = window.current_location()
            except:
                pass

        if event in (sg.WIN_CLOSED, "-CLOSE-"):
            break

        # --- Changement d'onglet ---
        if event == "-TABGROUP-":
            tab_key = values["-TABGROUP-"]  # ex: "-TAB-Statistical-"
            current_category = tab_key.replace("-TAB-", "").rstrip("-")
            window["-DETAILS-"].update("")

        # --- Sélection d'une ligne ---
        if isinstance(event, str) and event.startswith("-TABLE-") and current_category:
            try:
                selected = values[event]
                if not selected:
                    continue

                idx = values[event][0]

                if idx < 0 or idx >= len(events_by_cat[current_category]):
                    continue
                
                ev = events_by_cat[current_category][idx]

                # Clés utiles uniquement
                detail_keys = [
                    "Gene", "Event", "Position", "Depth", "PSI-like",
                    "Distribution", "p-value", "Significative",
                    "nbSignificantSamples", "nbFilteredSamples",
                    "cStart", "cEnd", "HGVS", "Source"
                ]

                details = "\n".join(
                    f"{k}: {ev[k]}" for k in detail_keys if k in ev
                )

                window["-DETAILS-"].update(details)

            except Exception as e:
                window["-STATUS-"].update(f"Erreur détails : {e}", text_color="red")
        
        elif ( isinstance(event, tuple) and isinstance(event[0], str) and event[0].startswith("-TABLE-") and event[1] == "+CLICKED+" and isinstance(event[2], tuple) and event[2][0] == -1 and current_category):        
            col_name = columns_by_cat[current_category][event[2][1]]
            ev_list = events_by_cat[current_category]
            print(col_name)
            print(ev_list)
            numeric = all(is_number(ev.get(col_name)) for ev in ev_list)
            print(numeric)
            sort_key = f"{current_category}_{col_name}"
            reverse = sort_states.get(sort_key, 0)

            # --- Tri numérique ---
            if numeric:
                ev_list.sort(key=lambda ev: ev.get(col_name, float("inf")), reverse = bool(reverse))

            # --- Tri position ---
            elif col_name.lower() == "position":
                ev_list.sort(key=lambda ev: parse_position(ev.get(col_name, "")), reverse=bool(reverse))

            # --- Tri texte ---
            else:
                ev_list.sort(key=lambda ev: str(ev.get(col_name, "")).lower(), reverse = bool(reverse))
            
            sort_states[sort_key] = 1 - reverse
                
            # Reconstruire les lignes
            new_values = []
            for ev in ev_list:
                row = []
                for c in columns_by_cat[current_category]:
                    if c + "_fmt" in ev:
                        row.append(ev[c + "_fmt"])
                    else:
                        row.append(ev.get(c, ""))
                new_values.append(row)
        
            window[event[0]].update(values=new_values)
            continue


        # --- QC ---
        if event == "-QC-RAW-":
            open_qc_html(qc_zip, "fastq_raw/", window, "FASTQ Raw QC", tmp_dir)

        if event == "-QC-TRIM-":
            open_qc_html(qc_zip, "fastq_trimmed/", window, "FASTQ Trimmed QC", tmp_dir)

        if event == "-QC-BAM-":
            open_qc_html(qc_zip, "BAM/", window, "BAM QC", tmp_dir)

        # --- Sashimi ---
        if event == "-SASHIMI-" and current_category:
            try:
                idx = values[f"-TABLE-{current_category}-"][0]
                ev = events_by_cat[current_category][idx]

                open_sashimi_plot(
                    sashimi_zip=sashimi_zip,
                    event=ev,
                    window=window,
                    tmp_dir=tmp_dir
                )

            except Exception as e:
                window["-STATUS-"].update(f"Erreur sashimi : {e}", text_color="red")

    window.close()
    return saved_size, saved_location
