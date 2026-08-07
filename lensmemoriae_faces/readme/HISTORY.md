## 19.0.1.0.1 (2026-08-07)

- Add enable/disable switch and configurable batch sizes for the scan and suggestion
  crons in the LensMemoriae settings.
- Add the _Exclude from Face Scan_ flag to skip individual images during automatic
  detection.
- Improve the scan cron to only re-process pending/error images (no endless re-scans of
  images without faces) and fail cleanly with a clear message when `face_recognition` is
  not installed.

## 19.0.1.0.0 (2026-06-12)

- Initial implementation: face detection, person grouping, face suggestions and
  identification workflows.