{
    "name": "LensMemoriae",
    "version": "19.0.1.0.27",
    "summary": "Recover the memory of photographs",
    "description": """
Recover the memory of your photographs: manage, tag, and share your images
directly from Odoo.

Main features:
- Tagging and filtering by categories
- Image moderation with approval workflow
- Geolocation with interactive Leaflet map
- Public gallery and self-registration
- Word cloud from approved notes
- Bulk tagging operations
""",
    "author": "Toni Carbonell Güell",
    "category": "Tools",
    "icon": "/lensmemoriae/static/description/icon.png",
    "depends": ["base", "mail", "web", "queue_job", "website"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "security/lensmemoriae_security.xml",
        "views/res_users_views.xml",
        "views/lensmemoriae_views.xml",
        "views/lensmemoriae_tag_views.xml",
        "views/mail_message_views.xml",
        "views/stop_word_views.xml",
        "views/arxiu_fons_views.xml",
        "views/arxiu_fons_wizard_views.xml",
        "views/lensmemoriae_menu.xml",
        "views/location_picker_views.xml",
        "views/bulk_tag_views.xml",
        "views/signup_template.xml",
        "views/homepage_template.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "lensmemoriae/static/src/scss/lensmemoriae.scss",
            "lensmemoriae/static/src/js/lensmemoriae.esm.js",
            "lensmemoriae/static/src/js/leaflet_map.esm.js",
            "lensmemoriae/static/src/js/wordcloud.esm.js",
            "lensmemoriae/static/src/xml/leaflet_map.xml",
            "lensmemoriae/static/src/xml/wordcloud.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
}
