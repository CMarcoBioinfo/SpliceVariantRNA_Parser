import os
import shutil
import PySimpleGUI as sg
from scripts.core.recap_parser import list_groups, list_samples
from scripts.core.tmp_manager import init_tmp_session, cleanup_tmp, init_qc_tmp, init_sashimi_tmp
from scripts.core.qc_manager import open_qc_html

import ctypes
import sys

def open_console():
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open("CONOUT$", "w")
    sys.stderr = open("CONOUT$", "w")

open_console()

def main():
    session_tmp = init_tmp_session()
    print("TMP global créé :", session_tmp)

    layout = [
        [sg.Text("Sélection du fichier SpliceVariantRNA recap (.zip)")],
        [sg.Input(key="-RUN-", enable_events=True), sg.FileBrowse("Parcourir")],

        [sg.Text("Groupe à analyser")],
        [sg.Combo([], key="-GROUP-", size=(40,1), readonly=True, enable_events=True)],

        [
            sg.Button("FASTQ Raw QC", key="-QC-RAW-", disabled=True),
            sg.Button("FASTQ Trimmed QC", key="-QC-TRIM-", disabled=True),
            sg.Button("BAM QC", key="-QC-BAM-", disabled=True),
        ],

        [sg.Text("Patient à analyser")],
        [sg.Input(key="-SEARCH-", enable_events=True, size=(40,1))],
        [sg.Combo([], key="-SAMPLE-", size=(40,1), readonly=True)],

        [sg.Button("Lancer l'analyse", key="-ANALYZE-")],
        [sg.Text("", key="-STATUS-", text_color="blue")],
        [sg.Text("by Corentin Marco", justification="right", font=("Helvetica", 8), text_color="gray")]
    ]

    window = sg.Window("SpliceVariantRNA Parser", layout, finalize=True, enable_close_attempted_event=True)
    window.metadata = {"current_run": None}

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, sg.WIN_CLOSED):
            break

        # --------------------------
        # Sélection du RUN
        # --------------------------
        if event == "-RUN-":
            run_path = values["-RUN-"]

            if not run_path:
                continue

            if not run_path.lower().endswith("recap.zip"):
                window["-STATUS-"].update("Veuillez sélectionner un fichier ZIP valide", text_color="red")
                continue

            run_id = os.path.splitext(os.path.basename(run_path))[0]
            print("Run sélectionné :", run_id)

            old_run = window.metadata["current_run"]
            if old_run and old_run != run_id:
                old_path = os.path.join(session_tmp, old_run)
                shutil.rmtree(old_path, ignore_errors=True)

            window.metadata["current_run"] = run_id

            # Lister les groupes
            groups = list_groups(run_path)
            window["-GROUP-"].update(values=groups) 
            window["-STATUS-"].update(f"{len(groups)} groupes trouvés", text_color="blue")

            # Construire la liste globale des patients (tous groupes confondus)
            all_samples = {}
            for group_zip in groups:
                samples = list_samples(run_path, group_zip)
                for s in samples:
                    all_samples[s] = group_zip

            window.metadata["all_samples"] = all_samples

            # TMP QC
            qc_tmp = init_qc_tmp(run_id)
            window.metadata["qc_tmp"] = qc_tmp
            print("QC TMP créé :", qc_tmp)

            # TMP sashimi
            sashimi_tmp = init_sashimi_tmp(run_id)
            print("Sashimi TMP créé :", sashimi_tmp)

            # QC ZIP
            run_dir = os.path.dirname(run_path)
            run_base = os.path.basename(run_path).replace("_recap.zip", "")
            qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")
            window.metadata["qc_zip"] = qc_zip

            if os.path.exists(qc_zip):
                window["-QC-RAW-"].update(disabled=False)
                window["-QC-TRIM-"].update(disabled=False)
                window["-QC-BAM-"].update(disabled=False)

        # --------------------------
        # Sélection d’un groupe
        # --------------------------
        if event == "-GROUP-":
            run_path = values["-RUN-"]
            group_zip = values["-GROUP-"]

            samples = list_samples(run_path, group_zip)
            window["-SAMPLE-"].update(values=samples)

            window["-STATUS-"].update(f"{len(samples)} patients trouvés", text_color="blue")

        # --------------------------
        # Recherche globale patient
        # --------------------------
        if event == "-SEARCH-":
            query = values["-SEARCH-"].lower()
            all_samples = window.metadata.get("all_samples", {})

            filtered = [s for s in all_samples if query in s.lower()]
            window["-SAMPLE-"].update(values=filtered)

            if len(filtered) == 1:
                sample = filtered[0]
                group_zip = all_samples[sample]

                window["-GROUP-"].update(values=list_groups(values["-RUN-"]), value=group_zip)

                run_path = values["-RUN-"]
                samples = list_samples(run_path, group_zip)
                window["-SAMPLE-"].update(values=samples)
                window["-SAMPLE-"].update(sample)

                print("group_zip =", repr(group_zip))
                print("groups =", [repr(g) for g in list_groups(values["-RUN-"])])
                print("match =", group_zip in list_groups(values["-RUN-"]))


        # --------------------------
        # QC RAW
        # --------------------------
        if event == "-QC-RAW-":
            qc_zip = window.metadata["qc_zip"]
            qc_tmp = window.metadata["qc_tmp"]
            open_qc_html(qc_zip, "fastq_raw/", window, "FASTQ Raw QC", qc_tmp)

        # --------------------------
        # QC TRIM
        # --------------------------
        if event == "-QC-TRIM-":
            qc_zip = window.metadata["qc_zip"]
            qc_tmp = window.metadata["qc_tmp"]
            open_qc_html(qc_zip, "fastq_trimmed/", window, "FASTQ Trimmed QC", qc_tmp)

        # --------------------------
        # QC BAM
        # --------------------------
        if event == "-QC-BAM-":
            qc_zip = window.metadata["qc_zip"]
            qc_tmp = window.metadata["qc_tmp"]
            open_qc_html(qc_zip, "BAM/", window, "BAM QC", qc_tmp)

    window.close()
    cleanup_tmp()

if __name__ == "__main__":
    main()
