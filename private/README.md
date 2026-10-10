# Local references and incoming configuration

Everything in this directory except this README is ignored by Git. The entire directory is excluded from the Docker build context.

Local layout:

- `CONTEXT.local.md`: known installation identifiers, without credentials.
- `reference/sma/`: original working openHAB packages, protocol regression harness and available captures.
- `reference/bmw/`: read-only C++/Homie baseline references.
- `incoming/openhab/`: place inverter/Home Manager Things, Items, transforms, rules and persistence exports here.

These local files are not transported by Git. If this repository is cloned on another host, supply the private inputs again through a private channel. Never commit passwords, tokens or unreviewed raw exports.
