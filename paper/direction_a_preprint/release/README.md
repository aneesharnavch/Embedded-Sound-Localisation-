# Rebuilding the source and data bundle

The generated `Direction_A_Source_and_Data/` directory and ZIP were removed during the September 2026 repository cleanup. Their scientific source and results remain in the project.

After installing the environment described in [REPRODUCING.md](../REPRODUCING.md), run from the project root:

```sh
.venv/bin/python -m validation.direction_a.package paper/direction_a_preprint/release/Direction_A_Source_and_Data --zip
```

This creates the directory and ZIP with a newly verified member checksum manifest. Both generated outputs are ignored by Git. This review-bundle command excludes the historical microphone recordings; the GitHub repository includes those recordings in their original folders.

`PACKAGE_VERIFICATION.json` and `Direction_A_Source_and_Data.zip.sha256` document the original author-review archive. They are retained as historical evidence, and are not checksums for a newly generated archive. Rebuilding after documentation changes or with different ZIP timestamps produces a different archive hash.
