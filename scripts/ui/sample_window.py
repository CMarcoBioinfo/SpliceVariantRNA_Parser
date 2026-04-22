import PySimpleGUI as sg
from scripts.core.qc_manager import open_qc_html
from scripts.core.sashimi_manager import open_sashimi_plot
from scripts.ui.events_manager import EventsManager


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

    # --- Gestionnaire externe ---
    manager = EventsManager(events_by_cat, columns_by_cat)

    # --- Catégorie active ---
    current_category = list(events_by_cat.keys())[0] if events_by_cat else None

    # -------------------------------------------------------------------------
    # CONSTRUCTION DES TABS
    # -------------------------------------------------------------------------

    tabs = []

    for cat_name in events_by_cat:

        cols = columns_by_cat.get(cat_name) or []
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

        tabs.append(sg.Tab(cat_name, [[table]], key=f"-TAB-{cat_name}-"))

    tab_group = sg.TabGroup(
        [tabs],
        key="-TABGROUP-",
        expand_x=True,
        expand_y=True,
        enable_events=True
    )

    # -------------------------------------------------------------------------
    # LAYOUT PRINCIPAL
    # -------------------------------------------------------------------------

    layout = [
        [tab_group],

        [sg.Column([
            [sg.Frame(
                f"Détails {patient_id}",
                [[sg.Multiline("", key="-DETAILS-", disabled=True, expand_x=True, expand_y=True)]],
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
        ], expand_x=True, expand_y=True)],

        [sg.Text("", key="-STATUS-", text_color="blue")]
    ]

    # -------------------------------------------------------------------------
    # CRÉATION FENÊTRE
    # -------------------------------------------------------------------------

    window = sg.Window(
        f"SpliceVariantRNA Viewer — {patient_id}",
        layout,
        resizable=True,
        finalize=True,
        enable_close_attempted_event=True,
        size=saved_size,
        location=saved_location
    )

    if saved_size is None:
        window.maximize()

    # -------------------------------------------------------------------------
    # BOUCLE ÉVÉNEMENTS
    # -------------------------------------------------------------------------

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "-CLOSE-"):
            break

        # --- Changement d'onglet ---
        if event == "-TABGROUP-":
            tab_key = values["-TABGROUP-"]
            current_category = tab_key.replace("-TAB-", "").rstrip("-")
            window["-DETAILS-"].update("")
            continue

        # --- Sélection d'une ligne ---
        if (
            isinstance(event, str)
            and event.startswith("-TABLE-")
            and current_category
        ):
            selected = values.get(event)
            if selected:
                idx = selected[0]
                details = manager.extract_details(current_category, idx)
                window["-DETAILS-"].update(details)
            continue

        # --- Tri ---
        if (
            isinstance(event, tuple)
            and isinstance(event[0], str)
            and event[0].startswith("-TABLE-")
            and event[1] == "+CLICKED+"
            and isinstance(event[2], tuple)
            and event[2][0] == -1
            and current_category
        ):
            cols = columns_by_cat.get(current_category) or []
            if not cols:
                continue

            col_name = cols[event[2][1]]
            new_values = manager.sort_category(current_category, col_name)
            window[event[0]].update(values=new_values)
            continue

        # --- QC ---
        if event == "-QC-RAW-":
            open_qc_html(qc_zip, "fastq_raw/", window, "FASTQ Raw QC", tmp_dir)
            continue

        if event == "-QC-TRIM-":
            open_qc_html(qc_zip, "fastq_trimmed/", window, "FASTQ Trimmed QC", tmp_dir)
            continue

        if event == "-QC-BAM-":
            open_qc_html(qc_zip, "BAM/", window, "BAM QC", tmp_dir)
            continue

        # --- Sashimi ---
        if event == "-SASHIMI-" and current_category:
            try:
                selected = values.get(f"-TABLE-{current_category}-")
                if not selected:
                    window["-STATUS-"].update("Aucun événement sélectionné", text_color="red")
                    continue

                idx = selected[0]
                ev = events_by_cat[current_category][idx]
                open_sashimi_plot(sashimi_zip, ev, window, tmp_dir)

            except Exception as e:
                window["-STATUS-"].update(f"Erreur sashimi : {e}", text_color="red")
            continue

    window.close()
    return saved_size, saved_location
