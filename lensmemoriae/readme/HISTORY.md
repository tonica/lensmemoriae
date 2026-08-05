## 19.0.1.0.8 (2026-08-06)

- Remove the filesystem scanning feature and everything related: the _Show Scan
  Directory button_ user setting, the _Scan Directory_ header button, the
  `scan_directory`/`action_scan` methods and the `/lens-memoriae/image/<path>`
  controller. Images are imported exclusively through the _Scrap_ wizard (XML) and the
  _Arxiu en Línia_ API download.

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
