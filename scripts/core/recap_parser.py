import zipfile
import io
import math
from python_calamine import CalamineWorkbook

SHEETS = {
    "Statistical Junctions": "Statistical",
    "Unique Junctions": "Unique",
    "Threshold Exceeded Junctions": "ThresholdExceeded",
    "No Model Junctions": "NoModel",
    "Event too complex": "TooComplex",
}

def format_float_sci(value):
    try:
        f = float(value)
    except:
        return value

    if f == 0:
        return "0"

    # Exposant basé sur la valeur brute
    exp = int(math.floor(math.log10(abs(f))))

    # Mantisse brute
    mantissa = f / (10 ** exp)

    # Mantisse arrondie à 2 décimales
    mantissa_str = f"{mantissa:.2f}".rstrip("0").rstrip(".")

    if exp == 0:
        return mantissa_str

    return f"{mantissa_str} × 10^{exp}"


# --------------------------
# GROUPES
# --------------------------

def list_groups(run_zip):
    """
    Retourne la liste des groupes *_recap.zip dans un run.
    """
    with zipfile.ZipFile(run_zip, "r") as z:
        return [
            f for f in z.namelist()
            if f.lower().endswith("_recap.zip")
        ]

# --------------------------
# PATIENTS
# --------------------------

def list_samples(run_zip, group_zip):
    """
    Retourne la liste des fichier .recap.xlsx dans un groupe interne.
    """
    with zipfile.ZipFile(run_zip, "r") as z:
        with z.open(group_zip) as inner:
            with zipfile.ZipFile(inner) as gz:
                return [
                    f for f in gz.namelist()
                    if f.lower().endswith(".recap.xlsx")
                ]

# --------------------------
# EXTRACTION XLSX
# --------------------------

def read_recap_from_zip(run_zip, group_zip, sample_file):
    """
    Ouvre le run.zip -> group.zip -> sample_file et retourne un BytesIO
    """
    with zipfile.ZipFile(run_zip, "r") as outer:
        inner_bytes = outer.read(group_zip)
        inner_buffer = io.BytesIO(inner_bytes)

        with zipfile.ZipFile(inner_buffer, "r") as inner:
            raw = inner.read(sample_file)
            return io.BytesIO(raw)

# --------------------------
# PARSING XLSX
# --------------------------

def parse_recap(run_zip, group_zip, sample_file):
    """
    Parse un fichier recap.xlsx via python_calamine.
    """
    bio = read_recap_from_zip(run_zip, group_zip, sample_file)
    wb = CalamineWorkbook.from_filelike(bio)

    rows_all = []

    for sheet_name, source_label in SHEETS.items():
        if sheet_name not in wb.sheet_names:
            continue

        sheet = wb.get_sheet_by_name(sheet_name)
        rows = sheet.to_python()

        if not rows:
            continue

        headers = rows[0]

        for row in rows[1:]:
            row_dict = {h: v for h, v in zip(headers, row)}
            row_dict["Source"] = source_label
            rows_all.append(row_dict)

    return rows_all


def row_to_event(row, sample_file):
    sample_name = sample_file.replace(".recap.xlsx", "")
    reads_col = sample_name
    psi_col = f"P_{sample_name}"

    chrom = row.get("chr")
    start = int(row.get("start"))
    end = int(row.get("end"))
    strand = row.get("strand")

    position = f"{chrom}:{start}-{end}" if chrom and start and end and strand else None

    p_raw = row.get("p_value")
    level = row.get("SignificanceLevel")
    
    if p_raw is None:
        p_raw = None
        pvalue_fmt = "nan"
    else:
        try:
            pvalue_raw = float(p_raw)
        except:
            pvalue_raw = None
        
        pvalue_fmt = format_float_sci(pvalue_raw)
        if level:
            pvalue_fmt = f"{pvalue_fmt} ({level})"

    psi_raw = row.get(psi_col)
    try:
        psi_value = float(psi_raw)
    except:
        psi_value = None

    psi_fmt = format_float_sci(psi_value) if psi_value is not None else None

    return {
        "Gene": row.get("Gene"),
        "Event": row.get("event_type"),
        "Position": position,

        # valeurs numériques (backend)
        "Depth": int(row.get(reads_col) or 0),
        "PSI-like": psi_value,
        "p-value": pvalue_raw,

        # valeurs formatées (frontend)
        "PSI-like_fmt": psi_fmt,
        "p-value_fmt": pvalue_fmt,

        "Distribution": row.get("DistribAjust"),
        "Significative": row.get("filterInterpretation") or row.get("Significative"),
        "nbSignificantSamples": int(row.get("nbSignificantSamples") or 0),
        "SampleReads": row.get("SampleReads"),
        "nbFilteredSamples": int(row.get("nbSampFilter") or 0),

        "cStart": row.get("cStart"),
        "cEnd": row.get("cEnd"),
        "HGVS": row.get("HGVS"),

        "Source": row.get("Source"),

        "Plots_links": {},
        "IGV_links": {},
    }
