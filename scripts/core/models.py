from dataclasses import dataclass

@dataclass
class PatientAnalysisResult:
    patient_id: str
    events_by_category: dict
    columns_by_category: dict
    qc_zip: str
    sashimi_zip: str | None
    tmp_dir: str
