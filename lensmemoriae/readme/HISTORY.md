## 19.0.1.0.7 (2026-08-05)

- Allow regular users to save the _Scrap_ wizard (`perm_write` on the wizard access
  rule).
- Rewrite `action_scrap` to process the XML export in batches with an incremental
  per-batch commit, `sudo` context and proper error logging, so large imports (e.g.
  50.000 elements) no longer abort or lose data.
- Let the superuser write image descriptions so bulk imports are not blocked by the
  moderator-only description check.

## 19.0.1.0.6 (2026-06-12)

- Initial implementation of the archival import, API image download, location picker,
  public gallery and self-registration features.
