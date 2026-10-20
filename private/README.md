# Private local records

Everything except this generic README is ignored by Git. The entire directory is
excluded from Docker build contexts and images. Back it up privately; a fresh clone
does not include these records. Never commit credentials, tokens or unreviewed exports.

- `CONTEXT.local.md`: local installation handoff; follow its private continuity pointers.
- `project-documentation/`: preserved installation reports, inventories, task diaries,
  acceptance evidence and active private follow-up.
- `reference/sma/`: original working packages and protocol references, read-only.
- `incoming/openhab/`: original Things/Items/rules/persistence exports, read-only.

Public contracts, neutral examples and reproducible checks belong under `docs/`.
Private originals must not be edited as part of public documentation maintenance.
See [privacy guidance](../docs/PRIVACY.md).
