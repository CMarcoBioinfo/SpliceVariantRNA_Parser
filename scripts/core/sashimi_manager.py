import os
import zipfile
import io
import subprocess

def find_sashimi_pdf(sashimi_zip, group_name, patient_id, sashimi_filename):
    """
    Version minimale basée sur ton ancien code.
    """
    # 1) ZIP du RUN
    with zipfile.ZipFile(sashimi_zip, "r") as z1:
        group_zip_name = f"{group_name}_sashimi.zip"
        if group_zip_name not in z1.namelist():
            return None

        group_bytes = z1.read(group_zip_name)
        group_buffer = io.BytesIO(group_bytes)

    # 2) ZIP du GROUPE
    with zipfile.ZipFile(group_buffer, "r") as z2:
        patient_zip_name = f"{patient_id}_sashimi.zip"
        if patient_zip_name not in z2.namelist():
            return None

        patient_bytes = z2.read(patient_zip_name)
        patient_buffer = io.BytesIO(patient_bytes)

    # 3) ZIP du PATIENT
    with zipfile.ZipFile(patient_buffer, "r") as z3:
        matches = [f for f in z3.namelist() if f.endswith(sashimi_filename)]
        if not matches:
            return None

        internal_pdf = matches[0]
        pdf_bytes = z3.read(internal_pdf)

    return pdf_bytes


def open_sashimi_plot(sashimi_zip, event, window, tmp_dir):
    """
    Version minimale : ouvre un sashimi déjà généré.
    """
    try:
        group_name = event.get("group_name")
        patient_id = event.get("patient_id")
        sashimi_filename = event.get("sashimi_filename")

        if not all([group_name, patient_id, sashimi_filename]):
            window["-STATUS-"].update("Métadonnées sashimi manquantes.", text_color="red")
            return

        pdf_bytes = find_sashimi_pdf(sashimi_zip, group_name, patient_id, sashimi_filename)

        if pdf_bytes is None:
            window["-STATUS-"].update("Sashimi introuvable.", text_color="red")
            return

        # Dossier temporaire
        out_dir = os.path.join(tmp_dir, "sashimi_plots", patient_id)
        os.makedirs(out_dir, exist_ok=True)

        out_path = os.path.join(out_dir, sashimi_filename)

        with open(out_path, "wb") as f:
            f.write(pdf_bytes)

        subprocess.Popen(f'explorer "{out_path}"')

    except Exception as e:
        window["-STATUS-"].update(f"Erreur sashimi : {e}", text_color="red")
