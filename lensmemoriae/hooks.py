def post_init_hook(env):
    env["lensmemoriae.image"].sudo().scan_directory()
    ICP = env["ir.config_parameter"].sudo()
    for key, val in [
        ("lensmemoriae.homepage_title", "Arxiu fotogràfic històric"),
        ("lensmemoriae.homepage_subtitle", "Explora el patrimoni visual digitalitzat"),
        ("lensmemoriae.public_blur_enabled", "True"),
        ("lensmemoriae.public_watermark_enabled", "True"),
        ("lensmemoriae.watermark_text", "Alfons Güell"),
        ("lensmemoriae.public_blur_intensity", "10"),
        ("lensmemoriae.public_watermark_opacity", "60"),
        ("lensmemoriae.public_watermark_font_scale", "20"),
        ("lensmemoriae.public_watermark_spacing_x", "2.5"),
        ("lensmemoriae.public_watermark_spacing_y", "3.0"),
        ("lensmemoriae.public_watermark_angle", "30"),
        ("lensmemoriae.public_jpeg_quality", "85"),
    ]:
        if not ICP.get_param(key):
            ICP.set_param(key, val)
    website = env["website"].search([], limit=1)
    if website:
        website.sudo().write({"homepage_url": "/lensmemoriae-home"})
    # Populate public_uid for existing records
    images = env["lensmemoriae.image"].sudo().search([("public_uid", "=", False)])
    if images:
        images._generate_public_uid()
