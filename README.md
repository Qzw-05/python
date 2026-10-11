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
- `revised_sections_7_9_certificates.json`: the encoded marking checks for the
  revised Sections 7–9 material.
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
revised_sections_7_9_certificates.json  Sections 7–9 certificate
infinite_transfer_certificates.json     infinite-transfer certificate
```

## Citation

If you use this code, cite the manuscript and this repository. The machine-
readable citation metadata is in [`CITATION.cff`](CITATION.cff).

## License

Add a license before public release. Choose the license that matches the
authors’ distribution requirements and commit the corresponding `LICENSE` file.
