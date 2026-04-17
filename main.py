import os
import shutil
import PySimpleGUI as sg
from scripts.core.tmp_manager import init_tmp_session, cleanup_tmp, init_qc_tmp, init_sashimi_tmp

def main():
    # Initialiser le TMP global
    session_tmp = init_tmp_session()
    print("TMP global créé :", session_tmp)
    
    # Fenêtre principale
    layout = [
        [sg.Text("Sélection du fichier SpliceVariantRNA recap (.zip)")],
        [sg.Input(key="-RUN-", enable_events=True), sg.FileBrowse("Parcourir")],

        [sg.Text("Groupe à analyser")],
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

    # Stocker le run courant
    window.metadata = {"current_run": None}

    # Boucle d'événements
    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, sg.WIN_CLOSED):
            break

        if event == "-RUN-":
            run_path = values["-RUN-"]

            if not run_path:
                continue

            if not run_path.lower().endswith("recap.zip"):
                window["-STATUS-"].update("Veuillez sélectionner un fichier ZIP valide", text_color="red")
                continue

            # Extraire un run_id
            run_id = os.path.splitext(os.path.basename(run_path))[0]
            print("Run sélectionné :", run_id)

            # Suppression du run précédant
            old_run = window.metadata["current_run"]
            if old_run and old_run != run_id:
                old_path = os.path.join(session_tmp, old_run)
                print("Suppression de l'ancien run TMP :", old_path)
                shutil.rmtree(old_path, ignore_errors=True)

            # Mise à jour du run courant
            window.metadata["current_run"] = run_id

            # Créer le dossier QC pour ce run
            qc_tmp = init_qc_tmp(run_id)
            print("QC TMP créé :", qc_tmp)

            # Créer le dossier sashimi pour ce run
            sashimi_tmp = init_sashimi_tmp(run_id)
            print("Sashimi TMP créé :", sashimi_tmp)

    window.close()
    cleanup_tmp()
    print("TMP global supprimé.")

if __name__ == "__main__":
    main()
