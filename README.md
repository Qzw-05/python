# U2 Kernel Constructive-Expansion Verification

This repository contains a reproducibility checker for the paper
**“U2 kernel constructive expansion”** and its revised Sections 7–9.
The checker verifies the finite kernel data, the marked constructive
expansions, the standard marking claims, and the infinite ladder-transfer
witnesses described in the paper.

The program is a verification supplement. It recomputes graph constructions,
perfect matchings, lonely edges, `Sigma` partitions, marking data, and explicit
witnesses, then writes JSON certificates. Passing the program confirms the
encoded finite cases and the tested parameter ranges; it does not replace the
paper's general mathematical arguments, induction, or external classification
theorems.

## Requirements

- Python 3.10 or newer
- `networkx==3.6.1`

The exact dependency is recorded in [`requirements.txt`](requirements.txt).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\\Scripts\\Activate.ps1
```

## Run all checks

From the repository root:

```bash
python verify_u2_all.py
```

The program asks where to save the four JSON certificates. Press Enter to use
the repository directory, or provide a directory explicitly:

```bash
python verify_u2_all.py --output-dir .
```

A successful run ends with:

```text
All four verification suites passed.
```

## Generated certificates

- `u2_finite_certificates.json`: finite kernels, lonely edges, `Sigma` partitions,
  child classes, parent identifications, and the length-four table.
- `marked_construction_certificates.json`: finite seed constructions and
  sampled infinite marked constructions.
- `revised_sections_7_9_certificates.json`: standard `E`, `C`, and `T` marking
  checks.
- `infinite_transfer_certificates.json`: local transfer tables, double-rung
  relations, and explicit infinite-family witnesses.

The JSON files in the repository are example certificates produced by a
successful run. They can be regenerated with the command above.

Every push and pull request is also checked by the GitHub Actions workflow in
`.github/workflows/verify.yml`.

## What is covered

| Component | Computational check |
|---|---|
| Finite kernels | `K4`, prism, bicorn, `T0`–`T3`, `D0`–`D2`, child classes and `Sigma` partitions |
| Marked constructions | Finite seeds and infinite samples with `r=2,...,10` |
| Revised Sections 7–9 | Finite marking cases and infinite samples with `r=2,...,12` |
| Infinite transfer | Local tables and explicit witnesses with `r=2,...,30`; full subset checks through `r=12` |

The paper's unrestricted general proof and any separate exhaustive enumeration
of all graphs are outside the scope of this script.

## Project layout

```text
verify_u2_all.py                         unified verification program
requirements.txt                         pinned Python dependency
u2_finite_certificates.json              finite verification certificate
marked_construction_certificates.json   marked-construction certificate
revised_sections_7_9_certificates.json  Sections 7–9 certificate
infinite_transfer_certificates.json     infinite-transfer certificate
```

## Reproducibility notes

The verification script encodes the graph labels and marking data used by the
paper, then independently recomputes the relevant assertions. The labels are
part of the certificate convention, so changing labels may change the JSON
presentation while preserving graph-isomorphism claims.

For a publication or archival release, record the Python and NetworkX versions
printed in `u2_finite_certificates.json`, retain the command output, and tag the
repository commit used to generate the certificates.

## Citation

If you use this code, cite the paper and this repository. A machine-readable
citation template is provided in [`CITATION.cff`](CITATION.cff).

## License

Choose and add a license before publication. If this repository is intended to
be distributed under the same terms as the template C program, add GPL-3.0 and
state that choice explicitly in this section.
