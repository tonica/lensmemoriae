Recover the memory of your photographs: LensMemoriae brings your photographs and their
archival metadata into Odoo and provides a rich, gallery-style interface to browse, tag,
moderate, geolocate and share them.

Main features:

- Import of archival metadata from a Catalan _Arxiu en Línia_ (gencat) XML export
  through the _Scrap_ wizard
- Fond download from _Arxiu en Línia_: search a fond by name and queue a background job
  that exports every document unit of the fond, generating one XML file per series plus
  combined CSV and JSON files
- Automatic image download from the _Arxiu en Línia_ API (cron + manual)
- Tagging with bulk add/remove from the kanban multi-select toolbar
- Moderation of image notes (pending/approved/rejected) with a moderation queue
- Moderation of image descriptions (only moderators can edit, with an approve/reject
  workflow)
- Geolocation with an interactive Leaflet map (form widget, location picker and a
  full-screen map view)
- Word cloud built from approved descriptions with configurable stop words
- Public gallery homepage with a rotating image carousel
- Public self-registration page (with honeypot and rate limiting)
- Protection of public thumbnails (blur, watermark and rate limiting)
- Kanban UI with a full-screen lightbox, card-size slider and multi-select bulk toolbar
