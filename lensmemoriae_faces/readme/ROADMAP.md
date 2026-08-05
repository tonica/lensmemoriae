- Expose the _Batch Identify_ wizard in the user interface (currently only the
  single-face wizard is reachable)
- Persist face thumbnails instead of recomputing them on every render
- Declare `face_recognition` as a graceful optional dependency and skip images cleanly
  when it is not installed
