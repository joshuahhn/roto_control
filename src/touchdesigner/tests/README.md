# Runtime tests

Follow [change-scoped validation](../../../AGENTS.md#change-scoped-validation).
During development run existing tests relevant to the changed behavior. Before
delivery of runtime source changes, run from `src/touchdesigner`:

```sh
python3 -m unittest discover -q
```

`tests/__init__.py` makes runtime fixtures, external scripts and scoped probes
importable during discovery. For affected Inspector behavior not covered by that
discovery, use its existing suite (or the relevant test module during development):

```sh
python3 -m unittest discover -s prototypes/inspector -q
```

A passing run on the final relevant source is sufficient; rerun after a relevant
change, failure or new evidence. Preserve wrong-target, stale ACK, persistence and
exactly-once coverage. Documentation-only changes require scoped diff/link/consistency
review and `git diff --check`; neither suite nor live acceptance is required.
