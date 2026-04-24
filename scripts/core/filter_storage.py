import os
import json
from pathlib import Path
import platform


class FilterStorageManager:
    """
    Gère l'enregistrement, le chargement, la suppression et la liste
    des filtres mono-colonne et globaux.
    Un fichier = un filtre.
    """

    def __init__(self, app_name="SpliceVariantRNA_Parser"):
        self.app_name = app_name

        # Dossiers personnels (APPDATA ou ~/.config)
        self.personal_dir = self._get_personal_dir()

        # Dossiers globaux (dans le dossier de l'exécutable)
        self.global_dir = Path(__file__).resolve().parent / f"filters_global_{app_name}"

        # Création des dossiers
        self.personal_dir.mkdir(parents=True, exist_ok=True)
        self.global_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # DÉTECTION DOSSIER PERSONNEL
    # ---------------------------------------------------------
    def _get_personal_dir(self):
        system = platform.system()

        if system == "Windows":
            base = Path(os.getenv("APPDATA")) / self.app_name
        else:
            base = Path.home() / ".config" / self.app_name

        return base / ".filters_personal"

    # ---------------------------------------------------------
    # OUTILS GÉNÉRIQUES
    # ---------------------------------------------------------
    def _get_scope_dir(self, scope):
        if scope == "personal":
            return self.personal_dir
        return self.global_dir

    def _sanitize_filename(self, name):
        """Supprime caractères interdits."""
        bad = '<>:"/\\|?*'
        for c in bad:
            name = name.replace(c, "_")
        return name.strip()

    def _load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ---------------------------------------------------------
    # LISTE DES FILTRES
    # ---------------------------------------------------------
    def list_filters(self, scope, filter_type=None, column=None):
        """
        Retourne la liste des fichiers JSON dans le scope.
        filter_type = "column" ou "global" ou None
        column = nom de colonne (pour filtrer les mono-colonnes)
        """
        folder = self._get_scope_dir(scope)
        results = []

        for file in folder.glob("*.json"):
            data = self._load_json(file)
            if not data:
                continue

            # Filtre par type
            if filter_type and data.get("type") != filter_type:
                continue

            # Filtre par colonne
            if filter_type == "column" and column:
                if data.get("column") != column:
                    continue

            results.append(file.stem)

        return sorted(results)

    # ---------------------------------------------------------
    # SAUVEGARDE FILTRE MONO-COLONNE
    # ---------------------------------------------------------
    def save_column_filter(self, column, name, blocks, scope):
        """
        Enregistre un filtre mono-colonne dans un fichier JSON.
        """
        folder = self._get_scope_dir(scope)
        name = self._sanitize_filename(name)
        path = folder / f"{name}.json"

        data = {
            "type": "column",
            "column": column,
            "blocks": blocks
        }

        self._save_json(path, data)
        return True

    # ---------------------------------------------------------
    # CHARGEMENT FILTRE MONO-COLONNE
    # ---------------------------------------------------------
    def load_column_filter(self, name, scope):
        folder = self._get_scope_dir(scope)
        path = folder / f"{name}.json"

        data = self._load_json(path)
        if not data or data.get("type") != "column":
            return None

        return data["column"], data["blocks"]

    # ---------------------------------------------------------
    # SUPPRESSION FILTRE MONO-COLONNE
    # ---------------------------------------------------------
    def delete_column_filter(self, name, scope):
        folder = self._get_scope_dir(scope)
        path = folder / f"{name}.json"

        if path.exists():
            path.unlink()
            return True
        return False

    # ---------------------------------------------------------
    # SAUVEGARDE FILTRE GLOBAL
    # ---------------------------------------------------------
    def save_global_filter(self, name, filters_dict, scope):
        """
        filters_dict = {col_name: blocks}
        """
        folder = self._get_scope_dir(scope)
        name = self._sanitize_filename(name)
        path = folder / f"{name}.json"

        data = {
            "type": "global",
            "filters": filters_dict
        }

        self._save_json(path, data)
        return True

    # ---------------------------------------------------------
    # CHARGEMENT FILTRE GLOBAL
    # ---------------------------------------------------------
    def load_global_filter(self, name, scope):
        folder = self._get_scope_dir(scope)
        path = folder / f"{name}.json"

        data = self._load_json(path)
        if not data or data.get("type") != "global":
            return None

        return data["filters"]

    # ---------------------------------------------------------
    # SUPPRESSION FILTRE GLOBAL
    # ---------------------------------------------------------
    def delete_global_filter(self, name, scope):
        folder = self._get_scope_dir(scope)
        path = folder / f"{name}.json"

        if path.exists():
            path.unlink()
            return True
        return False
