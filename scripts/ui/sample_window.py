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
            continue

        # --- CLIC SUR TABLEAU ---
        if (
            isinstance(event, tuple)
            and isinstance(event[0], str)
            and event[0].startswith("-TABLE-")
            and event[1] == "+CLICKED+"
            and isinstance(event[2], tuple)
        ):
            row = event[2][0]
            col = event[2][1]

            # --- Ligne 0 = filtres ---
            if row == 0:
                col_name = columns_by_cat[current_category][col]
                # Position de la fenêtre
                wx, wy = window.current_location()
                
                # Décalage vertical pour placer le popup sous la ligne 0
                popup_x = wx + 200
                popup_y = wy + 150
                
                value = sg.popup_get_text(
                    f"Filtre pour {col_name}",
                    keep_on_top=True,
                    location=(popup_x, popup_y)
                )

                manager.clear_filters(current_category, col_name)
                if value:
                    manager.add_filter(current_category, col_name, value)

                new_vals = manager.sort_category(current_category, 0)
                window[f"-TABLE-{current_category}-"].update(values=new_vals)
                continue

            # --- Tri ---
            if row == -1:
                col_index = col
                new_values = manager.sort_category(current_category, col_index)
                window[event[0]].update(values=new_values)
                continue

        # --- Sélection d'une ligne ---
        if isinstance(event, str) and event.startswith("-TABLE-") and current_category:
            try:
                selected = values[event]
                if not selected:
                    continue

                idx = selected[0]

                if idx == 0:
                    continue  # ligne de filtres

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
                idx = values[f"-TABLE-{current_category}-"][0]
                if idx == 0:
                    continue

                real_idx = idx - 1
                ev = manager.apply_filters(current_category)[real_idx]

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
