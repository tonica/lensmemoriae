{
    "name": "LensMemoriae Faces",
    "version": "19.0.1.0.0",
    "summary": "Automatic face detection and person identification in photographs",
    "description": """
Automatically detect, group, and identify faces in your LensMemoriae images.

Main features:
- Automatic face detection on image scan
- Person grouping and naming
- Batch face identification wizard
- Face-based image search and filtering
""",
    "author": "Toni Carbonell Güell",
    "category": "Tools",
    "depends": ["lensmemoriae"],
    # face_recognition is optional — code handles missing import gracefully
    "data": [
        "security/lensmemoriae_faces_security.xml",
        "security/ir.model.access.csv",
        "data/cron_data.xml",
        "views/lensmemoriae_person_views.xml",
        "views/lensmemoriae_face_views.xml",
        "views/lensmemoriae_image_views_inherit.xml",
        "views/lensmemoriae_faces_menu.xml",
        "views/lensmemoriae_face_identify_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "lensmemoriae_faces/static/src/scss/lensmemoriae_faces.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
