# Domain docs

This repo uses single-context domain documentation: root `GLOSSARY.md` and `docs/adr/`.

## Before exploring

Read the root glossary and ADRs relevant to the area being changed.
For TouchDesigner, also read its existing `CONTEXT.md` and `HANDOFF.md`, as required by `AGENTS.md`.

Missing glossary or ADR files are non-blocking: proceed silently.
The domain-modeling workflow creates them lazily when terminology or decisions are resolved.

## Consumer rules

- Use glossary vocabulary in issue titles, specifications, code and tests.
- When a concept is absent, check existing terminology before noting a glossary gap for domain-modeling.
- Identify proposals that contradict an existing ADR, including its number and the reason to reconsider it.
