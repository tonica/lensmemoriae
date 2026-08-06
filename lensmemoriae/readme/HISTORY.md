## 19.0.1.0.11 (2026-08-06)

- Render the _Recalculate Word Cloud_ list button with `display="always"` so it appears
  in the control panel instead of the Cog menu.

## 19.0.1.0.10 (2026-08-06)

- Show the _Recalculate Word Cloud_ button on the _Stop Words_ list header (it was only
  available on the record form), so moderators can resync the word cloud without opening
  a record.

## 19.0.1.0.9 (2026-08-06)

- Remove the deprecated _Generate Descriptions_ feature: the _Show Generate Descriptions
  button_ user setting, the _Generate Descriptions_ header button and the
  `action_generate_descriptions`/`_random_landscape_phrase` methods. Existing
  descriptions are kept; descriptions are now only provided by the XML _Scrap_ import or
  written by moderators.

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
