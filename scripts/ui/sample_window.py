import PySimpleGUI as sg
from scripts.core.qc_manager import open_qc_html
from scripts.core.sashimi_manager import open_sashimi_plot
from scripts.ui.events_manager import EventsManager
from scripts.ui.canvas_table import CanvasTable   # 🔥 nouveau


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

        # Canvas remplace sg.Table
        canvas = sg.Canvas(
            key=f"-CANVAS-{cat_name}-",
            size=(1000, 400),
            background_color="white",
            expand_x=True,
            expand_y=True
        )

        # Ligne de filtres (vrais Inputs)
        filter_inputs = [
            sg.Input(
                key=f"-FILTER-{cat_name}-{col}-",
                size=(12, 1),
                enable_events=True
            )
            for col in cols
        ]

        tabs.append(
            sg.Tab(cat_name, [
                [canvas],
                [*filter_inputs]   # 🔥 vraie ligne de filtres
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

    # --- Création des CanvasTable ---
    tables = {}
    for cat_name in events_by_cat.keys():
        canvas_elem = window[f"-CANVAS-{cat_name}-"]
        tk_canvas = canvas_elem.TKCanvas

        tables[cat_name] = CanvasTable(
            canvas=tk_canvas,
            columns=columns_by_cat[cat_name],
            data=manager.build_table_values(cat_name)
        )

        tables[cat_name].draw()

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

        # --- Filtres ---
        if isinstance(event, str) and event.startswith("-FILTER-"):
            _, _, cat, col, _ = event.split("-")
            value = values[event]

            manager.clear_filters(cat, col)

            if value.strip():
                manager.add_filter(cat, col, value.strip(), mode="AND")

            new_values = manager.sort_category(cat, 0)
            tables[cat].update_data(new_values)
            continue

        # --- Sélection d'une ligne ---
        if current_category:
            idx = tables[current_category].get_selected_index()
            if idx is not None:
                try:
                    details = manager.extract_details(current_category, idx)
                    window["-DETAILS-"].update(details)
                except Exception as e:
                    window["-STATUS-"].update(f"Erreur détails : {e}", text_color="red")

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
                idx = tables[current_category].get_selected_index()
                if idx is not None:
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
