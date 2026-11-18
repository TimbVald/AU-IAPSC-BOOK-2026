# AU-IAPSC BOOK 2026

Projet de génération du livre annuel des activités de l'AU-IAPSC à partir des
matrices d'activités mensuelles (.docm) et d'articles de référence.

## Environnement Python

- **Interpréteur de base** : `D:\Programs\Python315\python.exe` (Python 3.15.2)
  - ⚠️ L'installation d'origine (`%LOCALAPPDATA%\Python\pythoncore-3.15-64`)
    était verrouillée par un autre processus ; elle a été **copiée** vers
    `D:\Programs\Python315`. Ne pas supprimer l'original.
- **Environnement virtuel** : `.venv` à la racine du projet.

### Utilisation

```powershell
# Toujours utiliser l'interpréteur du venv (pas besoin d'activer)
.\.venv\Scripts\python.exe mon_script.py

# Ou activer le venv dans la session PowerShell
.\.venv\Scripts\Activate.ps1
python mon_script.py
```

### Dépendances

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Après installation de nouveaux packages :

```powershell
.\.venv\Scripts\python.exe -m pip freeze > requirements.txt
```

## WeasyPrint — dépendance système (Pango/GTK)

WeasyPrint a besoin des bibliothèques Pango/GLib. Elles sont installées dans
`C:\msys64\ucrt64\` (paquets MSYS2 UCRT64 extraits manuellement, sans admin).
WeasyPrint détecte ce dossier automatiquement.

Pour réinstaller ces bibliothèques :

```powershell
.\.venv\Scripts\python.exe tools\setup_weasyprint_runtime.py
```

## Arborescence

```
AU-IAPSC-BOOK-2026/
├── .venv/                  # environnement Python isolé
├── input/
│   ├── documents/          # documents sources (.docm, .pdf...)
│   ├── excel/              # fichiers Excel sources
│   ├── reference/          # documents de référence
│   └── images/             # images sources
├── data/
│   ├── raw/                # données extraites brutes
│   ├── processed/          # données nettoyées / structurées
│   └── statistics/         # données statistiques
├── src/
│   ├── extraction/         # extraction depuis .docm / .xlsx / .pdf
│   ├── analysis/           # analyse et structuration du contenu
│   ├── statistics/         # calculs statistiques
│   └── pdf_generation/     # génération du livre PDF
├── templates/
│   ├── cover/              # templates de couverture
│   ├── monthly/            # pages mensuelles
│   ├── statistics/         # pages statistiques
│   ├── articles/           # articles
│   └── components/         # composants réutilisables (Jinja2)
├── static/
│   ├── css/  fonts/  images/  logos/  charts/
├── output/
│   ├── drafts/             # brouillons
│   ├── final/              # versions finales
│   └── previews/           # aperçus / tests
├── tools/                  # scripts utilitaires (setup runtime, etc.)
├── doc/                    # matrices d'activités mensuelles sources
├── reference/              # document de référence annuel
├── requirements.txt
└── README.md
```

## Vérification de l'environnement

```powershell
.\.venv\Scripts\python.exe -c "import pandas, openpyxl, jinja2, matplotlib, PIL, pymupdf, pypdf, weasyprint; print('OK')"
```

Test PDF rapide : `output/previews/test_fr.pdf` (généré avec succès,
accents français vérifiés).

## Livre institutionnel 2026 (pipeline)

- Extraction : `.venv\Scripts\python.exe src\extraction\extract_docm.py`
- Stats : `.venv\Scripts\python.exe src\statistics\compute_stats.py` puis `make_charts.py`
- Donnees livre : `.venv\Scripts\python.exe src\analysis\build_book_data.py`
- Rendu livre : `.venv\Scripts\python.exe src\pdf_generation\build_book.py` → `output\final\AU-IAPSC_Livre_Activites_2026.pdf`