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
    click a word to filter the images that contain it.
6.  Moderators can approve or reject pending notes from the _Moderation Queue_ and
    manage the word cloud stop words under _LensMemoriae \> Stop Words_.
7.  The public gallery is available at `/lensmemoriae-home` and self registration at
    `/lens-memoriae/signup`.
8.  To download a whole fond from _Arxius en Línia_ (the Catalan Archives portal), go to
    _LensMemoriae \> Arxius en Línia \> Descarrega un fons_, type the fond name (e.g.
    "Alfons Güell, fotògraf"), pick a match and press _Descarrega_. The download runs in
    the background (queued job) and generates one XML file per series of the fond plus a
    combined CSV and JSON file. Download the files from the fond form: one XML per series
    via the _Sèries_ list, the CSV/JSON via the header buttons, or everything at once with
    the _Descarrega TOT (ZIP)_ button.

Maintenance actions for moderators are available as header buttons on the _Images_
screen:

- _Scrap_: import archival metadata from XML files (set a limit or leave 0 for no
  limit).
- _Download Pending_: download images pending from the _Arxiu en Línia_ API.
- _Clear All_: remove all images.
