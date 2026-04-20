import PySimpleGUI as sg
from scripts.core.qc_manager import open_qc_html
from scripts.core.sashimi_manager import open_sashimi_plot


def open_patient_window(result, saved_size=None, saved_location=None):
    """
    Fenêtre d'affichage des événements RNA pour un patient.
    """

    sg.theme("SystemDefault")

    # --- Données déjà préparées par l'orchestrator ---
    patient_id = result.patient_id
    events_by_cat = result.events_by_category
    columns_by_cat = result.columns_by_category
    qc_zip = result.qc_zip
    sashimi_zip = result.sashimi_zip
    tmp_dir = result.tmp_dir

    # --- Construction des onglets ---
    tabs = []
    for cat_name, events in events_by_cat.items():
        cols = columns_by_cat.get(cat_name, [])

        table = sg.Table(
            values=[[ev.get(col, "") for col in cols] for ev in events],
            headings=cols,
            key=f"-TABLE-{cat_name}-",
            auto_size_columns=True,
            enable_events=True,
            expand_x=True,
            expand_y=True,
            num_rows=12
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

    # --- Layout ---
    layout = [
        [tab_group],
        [
            [sg.Frame("Détails", [
                [sg.Multiline("", key="-DETAILS-", disabled=True, expand_x=True, expand_y=True)],
        [
            sg.Button("FASTQ Raw QC", key="-QC-RAW-"),
            sg.Button("FASTQ Trimmed QC", key="-QC-TRIM-"),
            sg.Button("BAM QC", key="-QC-BAM-"),
            sg.Button("Sashimi Plot", key="-SASHIMI-", disabled=(sashimi_zip is None)),
            sg.Button("Fermer", key="-CLOSE-"),
        ],
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

    # Catégorie active
    current_category = list(events_by_cat.keys())[0] if events_by_cat else None

    # --- Boucle événements ---
    while True:
        event, values = window.read()

        # Sauvegarde taille/position
        if window.TKroot is not None:
            try:
                saved_size = window.size
                saved_location = window.current_location()
            except:
                pass

        if event in (sg.WIN_CLOSED, "-CLOSE-"):
            break

        # Changement d'onglet
        if event == "-TABGROUP-":
            tab_key = values["-TABGROUP-"]
            current_category = tab_key.replace("-TAB-", "").replace("-", "")

        # Sélection d'une ligne
        if event.startswith("-TABLE-") and current_category:
            try:
                idx = values[event][0]
                ev = events_by_cat[current_category][idx]
                details = "\n".join(f"{k}: {v}" for k, v in ev.items())
                window["-DETAILS-"].update(details)
            except Exception as e:
                window["-STATUS-"].update(f"Erreur détails : {e}", text_color="red")

        # --- Boutons QC ---
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
