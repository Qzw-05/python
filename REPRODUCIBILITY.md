# Reproducing reference [8]

## Program identity and fixed version

- **Program:** Verification Supplement for Characterization of Cubic Graphs with Exactly Two Lonely Edges
- **Authors:** Zewei Qian and Pingshan Li
- **Entry point:** `verify_u2_all.py`
- **Version:** `1.0.1` (annotated Git tag `v1.0.1`)
- **Repository:** https://github.com/Qzw-05/python
- **Version link:** https://github.com/Qzw-05/python/tree/v1.0.1
- **Tested source commit before this metadata-only release:** `d6223819911284f62393d8c24273a49835694d98`

The release leaves `verify_u2_all.py` and `requirements.txt` unchanged.
The final release commit is obtained with `git rev-parse 'v1.0.1^{commit}'`.
Cite that complete commit hash as well as the version, using
`https://github.com/Qzw-05/python/tree/<FULL_RELEASE_COMMIT>`. A Git tag may be moved by a maintainer;
the full commit hash identifies the exact tree. No DOI is claimed.

## Requirements and commands

Use Git, Bash, Python 3.11 or newer, and `networkx==3.6.1`.
The exact Python and NetworkX versions used for the recorded run appear in
`evidence/reference8/environment.json`.

```bash
git clone https://github.com/Qzw-05/python.git u2-verification
cd u2-verification
git checkout --detach v1.0.1
git rev-parse HEAD
bash reproduce.sh
```

Check that `git rev-parse HEAD` equals the full commit cited in the paper.
For retrieval independent of the tag, replace `v1.0.1` above with that hash.
If needed, select the interpreter with
`PYTHON=python3.12 bash reproduce.sh`.
The script creates `.venv`, installs `requirements.txt`, and runs:

```bash
.venv/bin/python -I -u verify_u2_all.py --output-dir reproduced-certificates
```

On Git Bash, the virtual-environment interpreter is `.venv/Scripts/python.exe`;
`reproduce.sh` selects it automatically. Assertions must remain enabled:
do not run the verifier with `-O` or `-OO`. The runner uses `-I` so that
`PYTHONOPTIMIZE` cannot disable assertions through the environment.

## Successful output and evidence

A successful execution has exit status zero and ends with:

```text
All four verification suites passed.
```

The output directory contains:

1. `u2_finite_certificates.json`
2. `marked_construction_certificates.json`
3. `revised_sections_7_9_certificates.json`
4. `infinite_transfer_certificates.json`

`evidence/reference8/verification.log` records the release run;
`environment.json` records its command, source commit, versions, runtime, and
exit status. Absolute local repository paths in the log are replaced by
`<REPOSITORY>`. `certificates/` contains regenerated output, and
`certificate_comparison.json` compares its parsed JSON values with the four
original committed certificates. The publication script stops if any differ.
`SHA256SUMS.txt` records hashes of the program, dependency file, documentation,
original certificates, and run evidence. It excludes itself.

## Scope and limitations

The four suites implement the checks encoded in the original program:

- finite kernels, perfect matchings, lonely edges, Sigma partitions,
  triangle-contraction parents, isomorphism classes, and all ten
  length-four pattern representatives;
- marked construction checks, including samples with `2 <= r <= 10`
  and `t` in `{1,3}`;
- standard-marking checks on the finite seeds and samples with
  `2 <= r <= 12`, `t` in `{1,3}`;
- local and double-rung tables, and explicit witnesses for samples with
  `2 <= r <= 30`, `t` in `{1,3}`. For distinct-matching samples, the
  exhaustive subset check is used only for `r <= 12`; the JSON field
  `full_subset_check` records this distinction.

Passing these assertions verifies the encoded checks. Sampling an infinite
family does not prove the unrestricted statement for every parameter.
Providing a runnable release does not establish that a referee has audited
the authors' code. The accompanying mathematical proofs remain necessary.
