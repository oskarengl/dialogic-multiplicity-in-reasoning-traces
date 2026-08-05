# Vendored from NathanDuran/CAMS-Dialogue-Annotation

Retrieved 2026-07-22 from https://github.com/NathanDuran/CAMS-Dialogue-Annotation
(master branch), for the EXPLORATORY weighted-agreement reanalysis of Method 3.

Files:
- `da_labels_tree.json`         — the CAMS Dialogue Act hierarchy used to derive
                                  the label distance matrix (verbatim copy).
- `artstein_poesio_example.txt` — the 100-item, 2-coder fixture from
                                  Artstein & Poesio (2005), used by Duran et al.
                                  to validate their agreement code. Published
                                  expected values: alpha = 0.8156,
                                  alpha' = 0.8146, beta = 0.8163.

Citation:
Duran, N., Battle, S. & Smith, J. (2022). Inter-annotator Agreement Using the
Conversation Analysis Modelling Schema, for Dialogue. Communication Methods and
Measures. DOI: 10.1080/19312458.2021.2020229

These are inputs to `scripts/exploratory_weighted_agreement.py`. They are NOT
part of the pre-registered Method 3 gate.
