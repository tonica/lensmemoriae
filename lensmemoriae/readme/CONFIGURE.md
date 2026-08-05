The image base path is stored in the system parameter `lensmemoriae.base_path` (default
`/opt/odoo/custom/imatges`). Mount your image directory there (or change the parameter)
and run _Scan Directory_ from the _Images_ screen.

The _Scrap_ wizard reads XML files from the folder `/opt/odoo/custom/source`.

Go to _LensMemoriae \> Settings_ (available to administrators) to configure the
protection of public thumbnails:

- Blur: enable/disable and intensity
- Watermark: enable/disable, opacity, font scale, spacing and angle
- Watermark text
- JPEG output quality

Assign the _Moderator_ group to users who should approve or reject image notes and
descriptions, use the moderation queue and run maintenance actions.
