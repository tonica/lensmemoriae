**Arxius en Línia (descàrrega i importació)** — The fond list from the _Arxiu en Línia_
portal is fetched from the AENL API and cached in the
`lensmemoriae.aenl_fons_cache` system parameter, so no filesystem folder is involved.

1. Open _LensMemòria \> Arxius en Línia \> Descarrega un fons_ and type the fond name.
   Matching fonds are shown (from the cached list, searchable locally). Use
   _Actualitza llista de fons_ to refresh the cache, and _Mostra llista completa_ to
   browse it.
2. Tick the fonds to download and press _Descarrega_. The fond records are created in
   Odoo only at this point, and each fond fetches its document units from the API,
   generating one XML attachment per series plus CSV/JSON/ZIP files.
3. Open a fond and press **Importar a LensMemòria** to import all its series XML
   attachments into `lensmemariae.image`. Downloads are queued and processed by the
   image download cron.

Go to _LensMemòria \> Settings_ (available to administrators) to configure the
protection of public thumbnails and to refresh the fond list:

- Blur: enable/disable and intensity
- Watermark: enable/disable, opacity, font scale, spacing and angle
- Watermark text
- JPEG output quality
- Fond list refresh

Assign the _Moderator_ group to users who should approve or reject image notes and
descriptions, use the moderation queue and run maintenance actions.