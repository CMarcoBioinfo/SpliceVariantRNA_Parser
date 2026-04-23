import PySimpleGUI as sg
from scripts.core.qc_manager import open_qc_html
from scripts.core.sashimi_manager import open_sashimi_plot
from scripts.ui.events_manager import EventsManager


def open_patient_window(result, saved_size=None, saved_location=None):

    sg.theme("SystemDefault")

    # --- Données backend ---
    patient_id = result.patient_id
    events_by_cat = result.events_by_category
    columns_by_cat = result.columns_by_category
    qc_zip = result.qc_zip
    sashimi_zip = result.sashimi_zip
    tmp_dir = result.tmp_dir

    # --- Gestionnaire externe ---
    manager = EventsManager(events_by_cat, columns_by_cat)

    # --- Construction des onglets ---
    tabs = []
    for cat_name, events in events_by_cat.items():
        cols = columns_by_cat.get(cat_name, [])

        # Reconstruction initiale
        vals = manager.build_table_values(cat_name)

        table = sg.Table(
            values=vals,
            headings=cols,
            key=f"-TABLE-{cat_name}-",
            auto_size_columns=True,
            enable_events=True,
            enable_click_events=True,
            expand_x=True,
            expand_y=True,
            num_rows=15
        )

        # ---------------------------------------------------------
        # AJOUT FILTRES : ligne simple SOUS LE HEADER
        # ---------------------------------------------------------
        filter_row = [
            sg.Input(
                key=f"-FILTER-{cat_name}-{col}-",
                size=(12, 1),
                enable_events=True,
                justification="left"
            )
            for col in cols
        ]
        # ---------------------------------------------------------

        tabs.append(
            sg.Tab(cat_name, [
                [table],        # tableau (header inclus)
                filter_row      # 🔥 ligne de filtres juste en dessous
            ], key=f"-TAB-{cat_name}-")
        )

    tab_group = sg.TabGroup(
        [tabs],
        key="-TABGROUP-",
        expand_x=True,
        expand_y=True,
        enable_events=True
    )

    # --- Layout ---
    layout = [
        [tab_group],

        [sg.Column([
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
            tab_key = values["-TABGROUP-"]
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
        
                details = manager.extract_details(current_category, idx)
                window["-DETAILS-"].update(details)
        
            except Exception as e:
                window["-STATUS-"].update(f"Erreur détails : {e}", text_color="red")

        # ---------------------------------------------------------
        # AJOUT FILTRES : gestion des champs de filtre
        # ---------------------------------------------------------
        if isinstance(event, str) and event.startswith("-FILTER-"):
            # event = "-FILTER-cat-col-"
            _, _, cat, col, _ = event.split("-")

            value = values[event]

            # 1. effacer les filtres existants pour cette colonne
            manager.clear_filters(cat, col)

            # 2. si non vide → ajouter un filtre simple
            if value.strip():
                manager.add_filter(cat, col, value.strip(), mode="AND")

            # 3. appliquer filtres + tri
            new_values = manager.sort_category(cat, 0)

            # 4. mettre à jour la table
            window[f"-TABLE-{cat}-"].update(values=new_values)

            continue
        # ---------------------------------------------------------

        # --- TRI ---
        elif ( isinstance(event, tuple)
               and isinstance(event[0], str)
               and event[0].startswith("-TABLE-")
               and event[1] == "+CLICKED+"
               and isinstance(event[2], tuple)
               and event[2][0] == -1
               and current_category):
                   
            col_index = event[2][1]
        
            new_values = manager.sort_category(current_category, col_index)
        
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
