{
    "name": "LensMemoriae Visual Search",
    "version": "19.0.1.0.0",
    "summary": "Search similar photographs using perceptual hashing",
    "description": """
Search your LensMemoriae archive for visually similar photographs.

Main features:
- Paste an image (Ctrl+V) or attach a file to search by example
- Finds the source image even when only a part (crop) of it is pasted
- Region-based perceptual hashing index (whole image + tiles + overlapping windows)
- Visual Index management screen to monitor and rebuild the hash index
- Manual indexing per image and hashes shown in the image form view
    """,
    "author": "Toni Carbonell Güell",
    "category": "Tools",
    "depends": ["lensmemoriae"],
    "external_dependencies": {"python": ["imagehash", "PIL"]},
    "data": [
        "security/ir.model.access.csv",
        "data/cron_data.xml",
        "views/lensmemoriae_visualsearch_views.xml",
        "views/lensmemoriae_image_views_inherit.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "lensmemoriae_visualsearch/static/src/scss/visualsearch.scss",
            "lensmemoriae_visualsearch/static/src/js/visualsearch.esm.js",
            "lensmemoriae_visualsearch/static/src/js/visual_index.esm.js",
            "lensmemoriae_visualsearch/static/src/xml/visualsearch.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}