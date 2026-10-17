# TouchDesigner file map

Open [the current TD project](../projects/current/ROTO-CONTROL.toe); see
[project/archive index](../projects/README.md). Start with [README](../README.md) for use, [CONTEXT](../CONTEXT.md) for architecture
and the final [HANDOFF](../HANDOFF.md) entry for source/live acceptance status.

- [Function contracts](functions/) and [overview](overview.md): current user-facing
  Markdown, embedded by `scripts/td_project_docs.py` during TD build/upgrade.
- [Independent MIX analysis](functions/mix.md): current source slice and its
  distinction from the saved PLUGIN runtime.
- [Runtime Python](../code/py/roto_python/): controller, protocol, bindings and
  controller-owned Inspector lifecycle. Source files become embedded DATs.
- [Inspector source and builders](../prototypes/inspector/README.md): active compact
  Inspector model/commands/views still live here despite the historical folder name.
  Do not treat the entire directory as disposable prototype code.
- [Build/upgrade entry points](../scripts/build_network.py), [upgrade](../scripts/upgrade_network.py)
  and [scripts](../scripts/README.md): external Python, executed through live TD.
- [Runtime tests](../tests/README.md): test files under `tests/runtime`, discovered
  by the standard root unittest command.
- [Native runtime verifiers](../diagnostics/runtime/README.md): scoped live-TD scripts.
- [Current plans](plans/), [research](research/) and [historical plans/reports](history/):
  proposals, research and milestone evidence have separate destinations.
- [Diagnostics](../diagnostics/): scoped probes and results. Former root JSON/JSONL live in `diagnostics/runtime/results`; Inspector captures
  live in `diagnostics/inspector/results`. Original/new paths and byte hashes are
  recorded in `diagnostics/organization/artifact_moves.json`.
- [Current project and archives](../projects/README.md), plus [exports](../exports/):
  saved/recovery artifacts, saved/exported through live TD.

Source-only checks, from `src/touchdesigner`:

```sh
python3 -m unittest discover -q
python3 -m unittest discover -s prototypes/inspector -q
git diff --check
```

New files: runtime modules go beside the relevant runtime; current contracts go in
`docs/functions`; scoped investigation/profiling goes in `diagnostics/<topic>`;
finished development reports go in `docs/history`. Runtime tests live in `tests/runtime`; external build/upgrade/export entry points
live in `scripts`; native runtime verifiers live in `diagnostics/runtime`.
Keep the root for README/CONTEXT/HANDOFF, OPEN_PROJECT and requirements. Do not move embedded modules or probe
outputs without also updating their builders/writers and native acceptance.
