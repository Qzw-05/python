# Verification Supplement for “Characterization of Cubic Graphs with Exactly Two Lonely Edges”

This repository contains the computational supplement accompanying the manuscript
**“Characterization of Cubic Graphs with Exactly Two Lonely Edges”** by Zewei Qian
and Pingshan Li.

The program recomputes the finite graph constructions and the marked extensions
used in the manuscript. It is intended to make the finite cases and the stated
sampled families reproducible. A successful run is computational evidence for
the encoded cases; it does not replace the general mathematical proofs,
induction arguments, or classification results in the manuscript.

## Scope of the verification

The unified program covers the following material.

- **Finite kernels and Section 4.3 base cases:** construction of `K4`, the
  prism, the bicorn, `T0`–`T3`, `D0`–`D2`, the `Sigma` partitions, child
  isomorphism classes, parent identifications, and the length-four pattern
  table.
- **Marked constructions:** the finite seed graphs and the explicitly encoded
  infinite samples used to check the marking rules.
- **Further marking checks:** the finite and sampled cases recorded in the
   certificate file.
- **Infinite transfer checks:** local transfer tables, double-rung relations,
  and explicit witnesses for the tested ladder lengths.

The script does **not** prove the unrestricted statements of Lemmas 3.1,
3.5–3.7, 4.1, 4.4, or 4.19–4.21, and it does not constitute an exhaustive
computer enumeration of all cubic graphs.

<!-- BEGIN CURRENT MANUSCRIPT CROSSWALK -->
## Correspondence with the current four-section manuscript

This mapping follows the manuscript supplied on 10 November 2026. Its numbered
sections are 1 (Introduction), 2 (Preliminaries), 3 (The primitive kernels of
U2), and 4 (Characterization of U2). The conclusion is unnumbered.

**Historical numbering.** The phrase "Sections 7-9" (also written
"Sections 7--9" or "Sections 7–9") refers to an earlier organization of the
same project, not to sections of the current manuscript or to another paper.
The legacy certificate name `revised_sections_7_9_certificates.json` and the
internal function name `main_revised_sections` are retained for compatibility.
The current mathematical material is in Sections 4.2-4.4, with the finite
base-case computation in Lemma 4.16. The general induction in Section 4.4 is a
mathematical proof, not an additional computational verification suite.

| Program / certificate | Current manuscript location | What is actually checked |
| --- | --- | --- |
| `main_u2_kernels` / `u2_finite_certificates.json` | Lemma 3.7, Table 1; Lemma 3.8, Table 2 (Section 3.2); Lemma 3.12 (Section 3.3) | The finite one-step expansions of K4, the prism and bicorn; all ten length-four word representatives; the T0-T3 child classes, lonely edges, Sigma partitions and triangle-contraction parents used to identify D0-D2. This supplies finite checks, not a computer proof of the general parent/classification lemmas. |
| `main_marked_construction` / `marked_construction_certificates.json` | Lemmas 4.1-4.2, Proposition 4.4; Lemma 4.16; samples for Lemmas 4.17-4.18 | The ten finite seeds: matching type, complete zero-loss vertex set, noninterference, and the predicted matching type / zero-loss set after each allowed one-step expansion. Infinite-kernel samples: `2 <= r <= 10`, `t in {1,3}`, checking the seed matching type, zero-loss set and noninterference. |
| `main_revised_sections` / `revised_sections_7_9_certificates.json` | Section 4.2: Lemmas 4.8, 4.11, 4.13; Section 4.3: Lemmas 4.16-4.18 | Full standard markings on all ten finite seeds (Lemma 4.16), plus every E operation at the equal-type finite seeds and every C/T operation at the unequal-type finite seeds. Standard markings on infinite-kernel samples `2 <= r <= 12`, `t in {1,3}` (Lemmas 4.17-4.18). This infinite-sample loop checks the seed markings, not their E/C/T children. |
| `main_infinite_transfer` / `infinite_transfer_certificates.json` | Supporting checks for Lemmas 4.17-4.18 in Section 4.3 | Local/double-rung tables and explicit joins at inactive vertices, for `2 <= r <= 30`, `t in {1,3}`. For unequal-type samples, exhaustive multi-root subset checking is performed only for `r <= 12`; for larger r it is not performed (`full_subset_check: false`). Local transfer tables are supplementary checks, not separate numbered lemmas of the current manuscript. |

Stable LaTeX labels for the main correspondences are:

- Lemma 3.8: `lem:length4-kernels`; Table 2: `tab:length4`.
- Lemma 3.12: `lem:finite-certificate`.
- Lemma 4.8: `lem:operation-E`; Lemma 4.11: `lem:operation-C`;
  Lemma 4.13: `lem:operation-T`.
- Lemma 4.16: `lem:finite-seed-certificate`.
- Lemma 4.17: `lem:infinite-common-mark`.
- Lemma 4.18: `lem:infinite-unequal-mark`.

**Scope of the evidence.** Lemma 4.16 is the finite standard-marking base case;
Lemmas 4.17-4.18 concern infinite families and still require their mathematical
proofs. Theorem 4.19 combines these base cases. Theorems 4.20-4.21 establish
standard-marking completeness and complete generation by induction. Passing
finite or sampled checks does not prove these unrestricted statements or the
closure lemmas for every graph. This cross-reference patch changes only
explanatory text and one console message; certificate names, JSON contents,
verification assertions, graph constructions and parameter ranges are unchanged.
<!-- END CURRENT MANUSCRIPT CROSSWALK -->

## Requirements

- Python 3.11 or newer
- `networkx==3.6.1`

The dependency is pinned in [`requirements.txt`](requirements.txt). NetworkX
3.6.1 requires Python 3.11 or newer.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Run the verification

From the repository root:

```bash
python verify_u2_all.py
```

The program asks where to save the four certificate files. Press Enter to use
the repository directory, or pass a directory directly:

```bash
python verify_u2_all.py --output-dir .
```

A successful run ends with:

```text
All four verification suites passed.
```

The same command is run automatically by GitHub Actions on every push and pull
request. The workflow is in [`.github/workflows/verify.yml`](.github/workflows/verify.yml).

## Generated certificates

- `u2_finite_certificates.json`: finite kernels, lonely edges, `Sigma`
  partitions, child classes, parent identifications, and the length-four table.
- `marked_construction_certificates.json`: finite seed constructions and
  sampled marked constructions.
- `revised_sections_7_9_certificates.json`: standard-marking and finite-seed
  E/C/T checks for current Sections 4.2-4.3; see the correspondence table above.
- `infinite_transfer_certificates.json`: local transfer tables, double-rung
  relations, and explicit infinite-family witnesses.

The JSON files committed to the repository are certificates from a successful
run and can be regenerated with the command above. Graph labels are part of
the certificate convention; relabelling a graph can change the JSON display
without changing its isomorphism class.

## Project layout

```text
verify_u2_all.py                         unified verification program
requirements.txt                         pinned Python dependency
u2_finite_certificates.json              finite verification certificate
marked_construction_certificates.json   marked-construction certificate
revised_sections_7_9_certificates.json   standard-marking certificate (legacy filename)
infinite_transfer_certificates.json     infinite-transfer certificate
```

## Citation

If you use this code, cite the manuscript and this repository. The machine-
readable citation metadata is in [`CITATION.cff`](CITATION.cff).

## License

Add a license before public release. Choose the license that matches the
authors’ distribution requirements and commit the corresponding `LICENSE` file.


## Fixed version for manuscript reference [8]

Program: **Verification Supplement for Characterization of Cubic Graphs with Exactly Two Lonely Edges** (`verify_u2_all.py`).
Version: **1.0.1**, tag [`v1.0.1`](https://github.com/Qzw-05/python/tree/v1.0.1).
See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the fixed-version checkout,
requirements, exact commands, expected output, scope, and recorded evidence.
From a checkout of the cited version, run `bash reproduce.sh`.
Cite the full release commit as well as the version. Machine-readable
metadata are in [CITATION.cff](CITATION.cff).
