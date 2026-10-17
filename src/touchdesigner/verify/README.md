# Native TouchDesigner verification

These general runtime verifiers execute inside live TD with each script's
explicit source/controller inputs. Pass `src/touchdesigner` as the source root,
not this directory. Inspect the verifier before running it: some create
fixtures, configure mappings, write results or require a staged callback.

Existing results stay in `diagnostics/runtime/results/`. Topic-specific
diagnostics stay with their fixtures, including Python portability and binding
takeover. Historical evidence retains its original paths and acceptance scope.

Follow [change-scoped validation](../../../AGENTS.md#change-scoped-validation).
