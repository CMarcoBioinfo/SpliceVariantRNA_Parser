import os
from scripts.core.models import PatientAnalysisResult
from scripts.core.recap_parser import parse_recap, row_to_event
from scripts.core.tmp_manager import init_sashimi_tmp


COLUMNS_BY_SOURCE = {
    "Statistical": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbSignificantSamples"],
    "Unique": ["Gene", "Event", "Position", "Depth", "PSI-like", "p-value", "nbFilteredSamples"],
    "ThresholdExceeded": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "NoModel": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
    "TooComplex": ["Gene", "Event", "Position", "Depth", "nbFilteredSamples"],
}


def normalize_source(s: str) -> str:
    return s.strip().replace(" ", "").lower()


def analyze_patient(run_path, group_zip, sample, session_tmp):
    # 1) Lire recap
    rows = parse_recap(run_path, group_zip, sample)
    events = [row_to_event(r, sample) for r in rows]

    # 2) Normaliser sources
    for ev in events:
        if "Source" in ev:
            ev["Source"] = normalize_source(ev["Source"])

    # 3) Regrouper
    events_by_cat = {normalize_source(k): [] for k in COLUMNS_BY_SOURCE}
    for ev in events:
        src = ev.get("Source", "")
        if src in events_by_cat:
            events_by_cat[src].append(ev)

    # 4) Colonnes
    columns_by_cat = {
        normalize_source(k): v
        for k, v in COLUMNS_BY_SOURCE.items()
    }

    # 5) QC ZIP
    run_dir = os.path.dirname(run_path)
    run_base = os.path.basename(run_path).replace("_recap.zip", "")
    qc_zip = os.path.join(run_dir, f"{run_base}_qc.zip")

    # 6) Sashimi ZIP
    sashimi_zip = os.path.join(run_dir, f"{run_base}_sashimi.zip")
    if not os.path.exists(sashimi_zip):
        sashimi_zip = None

    # 7) Métadonnées sashimi
    for ev in events:
        ev["group_name"] = group_zip.replace(".zip", "").replace("_recap", "")
        ev["patient_id"] = sample.replace(".recap.xlsx", "")

        if "Position" in ev and "Gene" in ev:
            try:
                chrom, coords = ev["Position"].split(":")
                start, end = coords.split("-")
                ev["sashimi_filename"] = f"{chrom}_{start}_{end}_{ev['Gene']}.pdf"
            except:
                ev["sashimi_filename"] = None

    # 8) Dossier sashimi correct
    run_id = run_base
    tmp_sashimi = init_sashimi_tmp(run_id)

    return PatientAnalysisResult(
        patient_id=sample,
        events_by_category=events_by_cat,
        columns_by_category=columns_by_cat,
        qc_zip=qc_zip,
        sashimi_zip=sashimi_zip,
        tmp_dir=tmp_sashimi
    )
