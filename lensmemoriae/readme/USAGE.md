To use LensMemoriae:

1.  Go to _LensMemoriae \> Images_ to browse all indexed images in the gallery. Use the
    card-size slider to adjust the grid and the lightbox to view full resolution images.
    Select several images to add or remove tags in bulk.
2.  Click an image to open its detail view: view tags, approved notes, the interactive
    map, the description and the XML metadata imported from the archive.
3.  On the image form, use _Set Location_ to place the image on the map.
4.  Use _LensMemoriae \> Map_ to explore all geolocated images on a full-screen Leaflet
    map.
5.  Use _LensMemoriae \> Word Cloud_ to visualize the words of approved descriptions;
    use the slider in the toolbar to choose how many words to display (from 1 to all
    available active stop words, 80 by default) and click a word to filter the images
    that contain it.
6.  Moderators can approve or reject pending notes from the _Moderation Queue_ and
    manage the word cloud stop words under _LensMemoriae \> Stop Words_.
7.  The public gallery is available at `/lensmemoriae-home` and self registration at
    `/lens-memoriae/signup`.
8.  To download a whole fond from _Arxius en Línia_ (the Catalan Archives portal), go to
    _LensMemoriae \> Arxius en Línia \> Descarrega un fons_ and type the fond name (e.g.
    "Alfons Güell, fotògraf"). Matching fonds are listed from the cached full fond list;
    use _Actualitza llista de fons_ to refresh it or _Mostra llista completa_ to browse.
    Tick the fonds you want and press _Descarrega_: the foundations in Odoo and the
    download runs in the background (queued job), generating one XML attachment per
    series of the fond plus combined CSV and JSON files. Download files from the fond
    form: one XML per series via the _Sèries_ list, the CSV/JSON via the header buttons,
    or everything at once with _Descarrega TOT (ZIP)_.
9.  On the fond form, press **Importar a LensMemòria** to import all its series XML
    attachments into the image archive. Image downloads are queued and processed by the
    download cron.

Maintenance actions for moderators are available as header buttons on the _Images_
screen:

- _Download Pending_: download images pending from the _Arxiu en Línia_ API.
- _Clear All_: remove all images.