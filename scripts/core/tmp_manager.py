import tempfile
import shutil
import os

# Dossier racine TMP
_SESSION_TMP = None

def init_tmp_session(prefix = "SpliceVariantRNA_Parser_session_"):
    """
    Crée un dossier temporaire global unique pour la session.
    """
    global _SESSION_TMP

    _SESSION_TMP = tempfile.mkdtemp(prefix = prefix)
    return _SESSION_TMP

def get_session_tmp():
    """
    Retourne le dossier racine de la session.
    """
    return _SESSION_TMP

def init_qc_tmp(run_id):
    """
    Crée le dossier QC pour un run.
    """
    qc_tmp = os.path.join(_SESSION_TMP, run_id, "qc")
    os.makedirs(qc_tmp, exist_ok=True)
    return qc_tmp

def get_qc_tmp(run_id):
    """
    Retourne le dossier QC de la run.
    """
    return os.path.join(_SESSION_TMP, run_id, "qc")

def init_sashimi_tmp(run_id):
    """
    Crée le dossier sashimi pour un run.
    """
    sashimi_tmp = os.path.join(_SESSION_TMP, run_id, "sashimi")
    os.makedirs(sashimi_tmp, exist_ok=True)
    return sashimi_tmp

def get_sashimi_tmp(run_id):
    """
    Retourne le dossier sashimi de la run.
    """
    return os.path.join(_SESSION_TMP, run_id, "sashimi")

def cleanup_tmp():
    """
    Supprime entièrement le dossier temporaire global.
    """
    global _SESSION_TMP

    if _SESSION_TMP and os.path.exists(_SESSION_TMP):
        shutil.rmtree(_SESSION_TMP, ignore_errors=True)

    _SESSION_TMP = None
