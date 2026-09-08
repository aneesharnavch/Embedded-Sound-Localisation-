# Baseline snapshot after repository cleanup

The 7 September 2026 full-project archive was removed on 9 September 2026 to avoid storing another copy of the project and recordings. Before removal, all 1,102 archived files were compared with the working files: 1,099 were byte-identical, and three were older versions of documents.

Those three original document versions are retained under `original_documents/`, using their original project-relative paths:

- `HANDOVER.md`
- `paper/publication_speedrun/ACTA_ACUSTICA_ROUTE_A_PLAN.md`
- `paper/publication_speedrun/DIRECTION_A_PREPRINT_TODO.md`

`manifest.json` remains the original historical inventory and checksum record. It describes the pre-execution workspace, including duplicates and downloaded files removed during cleanup; it is not a manifest of the cleaned repository. Old execution-log references to `pre_execution_2026-09-07.tar.gz` refer to the removed snapshot.

The separate superseded v1 scientific source, configurations, estimates, and diagnostics remain under `../superseded/v1_duration_0p9/`. Only its optional response cache and document build intermediates were removed.
