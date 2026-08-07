The optional Python package `imagehash` (with `Pillow`) must be installed in the Odoo
environment for visual search to work. In this Doodba setup add it to the
`PIP_INSTALL_ODOO` build argument (for example `"face_recognition imagehash"`) and
rebuild the image. Without it the module still installs, but no hashes can be computed.

Images must be *downloaded* before they can be indexed (the perceptual hash is computed
from the stored binary). Indexing runs automatically by cron every 15 minutes on
pending images.

Indexed hashes are readable by regular users; only moderators can (re)build them.