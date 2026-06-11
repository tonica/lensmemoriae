import base64
import json
import logging
import mimetypes
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime

import requests
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LensMemoriaeTag(models.Model):
    _name = "lensmemoriae.tag"
    _description = "LensMemoriae Tag"
    _order = "name"

    name = fields.Char(string="Tag", required=True)
    color = fields.Char()


class LensMemoriaeImage(models.Model):
    _name = "lensmemoriae.image"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "LensMemoriae Image"
    _order = "mtime desc, name"
    _rec_name = "name"
    _relpath_unique = models.Constraint(
        "UNIQUE (relpath)", "Relative path must be unique!"
    )
    _codi_referencia_unique = models.Constraint(
        "UNIQUE (codi_referencia)", "Codi referència must be unique!"
    )

    name = fields.Char(required=True)
    relpath = fields.Char(string="Relative Path", required=False, index=True)
    image = fields.Binary(attachment=False)
    image_download_state = fields.Selection(
        [
            ("pending", "Pending Download"),
            ("downloading", "Downloading"),
            ("downloaded", "Downloaded"),
            ("error", "Error"),
        ],
        default="pending",
        string="Download State",
    )
    download_progress = fields.Float(
        compute="_compute_download_progress",
        group_operator=False,
    )
    file_size = fields.Integer(string="File Size (bytes)")
    mtime = fields.Datetime(string="Modification Time")
    mimetype = fields.Char(string="MIME Type")
    tag_ids = fields.Many2many("lensmemoriae.tag", string="Tags")
    latitude = fields.Float(digits=(9, 6))
    longitude = fields.Float(digits=(9, 6))
    approved_notes = fields.Html(compute="_compute_approved_notes")
    description = fields.Text()
    description_approved = fields.Boolean(default=False)
    is_moderator = fields.Boolean(compute="_compute_is_moderator")
    public_uid = fields.Char(index=True, string="Public UID")

    codi_referencia = fields.Char(string="Codi Referència", index=True)
    codi_grup = fields.Char()
    arxiu = fields.Char()
    codi_arxiu = fields.Char()
    fons = fields.Char()
    codi_fons = fields.Char()
    tipus_unitat = fields.Char()
    cod_unitat = fields.Char()
    unitat_installacio = fields.Char()
    nivell_descripcio = fields.Char()
    titol_unitat_documental = fields.Char()
    cronologia = fields.Char()
    data_inici = fields.Char()
    continu_discontinu = fields.Char()
    data_fi = fields.Char()
    sense_data = fields.Char()
    classificacio = fields.Char()
    codi_classificacio = fields.Char()
    procedencia = fields.Char()
    codi_procedencia = fields.Char()
    serie_cataleg = fields.Char()
    codi_serie_cataleg = fields.Char()
    expedient_inicial = fields.Char()
    expedient_final = fields.Char()
    xml_descripcio = fields.Text(string="XML Description")
    observacions = fields.Text()
    reportatge = fields.Char()
    volum = fields.Char()
    exemplars = fields.Char()
    autoria = fields.Char()
    onomastics = fields.Char()
    toponimics = fields.Char()
    llogaret = fields.Char()
    lloc_precis = fields.Char()
    municipi_longitud = fields.Char()
    municipi_latitud = fields.Char()
    llogaret_longitud = fields.Char()
    llogaret_latitud = fields.Char()
    tematics = fields.Char()
    generes = fields.Char()
    editors = fields.Char()
    impremta = fields.Char()
    diposit_legal = fields.Char()
    total_objectes_digitals = fields.Integer()
    codi_reprografia = fields.Char()
    data_publicacio = fields.Char()
    data_descarrega = fields.Char()
    enllac_objecte_digital = fields.Char()

    @api.depends_context("uid")
    def _compute_is_moderator(self):
        is_mod = self.env.user.has_group("lensmemoriae.group_moderator")
        for rec in self:
            rec.is_moderator = is_mod

    def _compute_approved_notes(self):
        for rec in self:
            notes = self.env["mail.message"].search(
                [
                    ("model", "=", "lensmemoriae.image"),
                    ("res_id", "=", rec.id),
                    ("moderation_state", "=", "approved"),
                ],
                order="create_date desc",
            )
            rec.approved_notes = (
                "<br/>".join(note.body or "" for note in notes) or False
            )

    @api.model
    def _get_thumbnail_secret(self):
        ICP = self.env["ir.config_parameter"].sudo()
        secret = ICP.get_param("lensmemoriae.thumbnail_secret")
        if not secret:
            import secrets

            secret = secrets.token_hex(32)
            ICP.set_param("lensmemoriae.thumbnail_secret", secret)
        return secret

    def _generate_public_uid(self):
        import hashlib
        import hmac

        secret = self._get_thumbnail_secret()
        for rec in self:
            if not rec.public_uid:
                uid = hmac.new(
                    secret.encode(),
                    str(rec.id).encode(),
                    hashlib.sha256,
                ).hexdigest()[:12]
                rec.write({"public_uid": uid})

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.public_uid:
                rec._generate_public_uid()
        return recs

    def write(self, vals):
        if "description" in vals and not self.env.user.has_group(
            "lensmemoriae.group_moderator"
        ):
            raise UserError(
                self.env._("Only moderators can edit the description of an image.")
            )
        return super().write(vals)

    def action_approve_description(self):
        self.ensure_one()
        self.write({"description_approved": True})
        return True

    def action_reject_description(self):
        self.ensure_one()
        self.write({"description_approved": False})
        return True

    @api.model
    def _compute_words_from_descriptions(self):
        from collections import defaultdict

        images = self.search(
            [("description_approved", "=", True), ("description", "!=", False)]
        )

        STOP_WORDS = {
            "de",
            "la",
            "el",
            "en",
            "un",
            "una",
            "per",
            "amb",
            "del",
            "les",
            "els",
            "al",
            "d",
            "l",
            "s",
            "i",
            "a",
            "que",
            "es",
            "no",
            "se",
            "lo",
            "los",
            "las",
            "le",
            "y",
            "e",
            "o",
            "u",
            "su",
            "me",
            "te",
            "por",
            "con",
            "sin",
            "como",
            "mas",
            "pero",
            "este",
            "esta",
            "esto",
            "més",
            "molt",
            "ben",
            "força",
            "poc",
            "gaire",
            "quan",
            "on",
            "com",
            "tot",
            "tota",
            "totes",
            "tots",
            "entre",
            "contra",
            "fins",
            "durant",
            "mitjançant",
            "segons",
            "sense",
            "dins",
            "fora",
            "damunt",
            "davant",
            "darrere",
            "sota",
            "prop",
            "lluny",
            "aquest",
            "aquesta",
            "aquests",
            "aquestes",
            "aixo",
            "açò",
            "aquell",
            "aquella",
            "aquells",
            "aquelles",
            "així",
            "també",
            "si",
            "ni",
            "ja",
            "encara",
            "sempre",
            "mai",
            "potser",
            "només",
            "solament",
            "gairebé",
            "almenys",
            "aproximadament",
            "just",
            "exactament",
            "ets",
            "als",
            "pels",
            "dels",
            "mateix",
            "mateixa",
            "altres",
            "altre",
            "cada",
            "seu",
            "seva",
            "seus",
            "seves",
            "meu",
            "meva",
            "teu",
            "teva",
        }

        word_total = Counter()
        word_images = defaultdict(set)

        for img in images:
            tokens = re.findall(r"[a-zàèéíòóúïüç']+", (img.description or "").lower())
            filtered = [t for t in tokens if len(t) >= 3 and t not in STOP_WORDS]
            word_total.update(filtered)
            for t in set(filtered):
                word_images[t].add(img.id)

        return [
            (w, c, len(word_images[w])) for w, c in word_total.most_common() if c > 1
        ]

    @api.model
    def get_views(self, views, options=None):
        result = super().get_views(views, options=options)
        for view_type, view_data in result.get("views", {}).items():
            if view_type in ("list", "kanban") and "arch" in view_data:
                arch_before = view_data["arch"]
                arch_after = self.env["ir.ui.view"]._lensmemoriae_filter_header_buttons(
                    arch_before
                )
                _logger.info(
                    "=== get_views %s ===\nBEFORE: %s\nAFTER: %s",
                    view_type,
                    etree.tostring(
                        etree.fromstring(arch_before), pretty_print=True
                    ).decode(),
                    etree.tostring(
                        etree.fromstring(arch_after), pretty_print=True
                    ).decode(),
                )
                view_data["arch"] = arch_after
        return result

    @api.model
    def get_word_cloud_data(self):
        StopWord = self.env["lensmemoriae.stop.word"].sudo()
        active = StopWord.search([("active", "=", True)], order="count desc", limit=80)
        if active:
            return [{"word": w.name, "count": w.count} for w in active]

        last = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lensmemoriae.wordcloud_cache")
        )
        if last:
            try:
                return json.loads(last)
            except Exception:
                pass

        words_data = self._compute_words_from_descriptions()
        vals_list = [
            {"name": w, "count": c, "image_count": ic, "active": True}
            for w, c, ic in words_data
        ]
        if vals_list:
            StopWord.create(vals_list)

        return [{"word": w, "count": c} for w, c, ic in words_data[:80]]

    def _random_landscape_phrase(self):
        nouns = [
            "muntanya",
            "vall",
            "bosc",
            "riu",
            "llac",
            "costa",
            "platja",
            "turó",
            "prat",
            "camp",
            "serra",
            "penya-segat",
            "cascada",
            "erm",
            "plana",
            "congost",
            "torrent",
            "cala",
            "illa",
            "mar",
            "albufera",
            "delta",
            "golf",
            "puig",
            "barranc",
            "devesa",
            "mirador",
            "rovira",
            "cim",
            "cresta",
            "gorga",
            "estany",
        ]
        adjs = [
            "tranquil·la",
            "imponent",
            "serena",
            "verda",
            "daurada",
            "espectacular",
            "pintoresca",
            "màgica",
            "vast",
            "frondosa",
            "rocallosa",
            "ondulada",
            "feréstega",
            "idíl·lica",
            "assolellada",
            "boirosa",
            "nevada",
            "abrupta",
            "plàcida",
            "escarpada",
            "silenciosa",
            "ombrada",
            "infinita",
            "seductora",
        ]
        moments = [
            "la posta de sol",
            "l'alba",
            "migdia",
            "el capvespre",
            "el matí",
            "la tarda",
            "el crepuscle",
            "l'ocàs",
            "l'hora blava",
            "la llum del migdia",
        ]
        weathers = [
            "cel clar",
            "cel ennuvolat",
            "cel rosat",
            "cel ataronjat",
            "cel blau",
            "cel estrellat",
            "cel radiant",
            "cel serè",
            "cel grisenc",
            "cel lluminós",
            "cel de tempesta",
            "cel de posta",
            "cel d'hivern",
        ]
        tpls = [
            "Vista panoràmica de {adj} {noun} a {moment}.",
            "{noun} {adj} sota un {weather}.",
            "Paisatge de {noun} {adj} durant {moment}.",
            "{adj} {noun} banyada per la llum de {moment}.",
            "Vista de {adj} {noun} amb {weather}.",
            "{noun} {adj} enmig d'un paisatge de somni — {moment}.",
            "{adj} {noun} que s'estén fins on arriba la vista.",
            "Recòrner de {noun} {adj} il·luminat per {moment}.",
            "{noun} de contorn {adj} sota un {weather}.",
            "{adj} {noun} amb {moment} de fons.",
        ]
        tpl = random.choice(tpls)
        return tpl.format(
            noun=random.choice(nouns),
            adj=random.choice(adjs),
            moment=random.choice(moments),
            weather=random.choice(weathers),
        )

    def action_generate_descriptions(self):
        images = self.search([("description", "=", False)])
        count = 0
        for img in images:
            phrase = self._random_landscape_phrase()
            img.write({"description": phrase, "description_approved": True})
            count += 1
        if not count:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Info",
                    "message": "Totes les imatges ja tenen descripció.",
                    "type": "info",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Descripcions Generades",
                "message": f"S'han generat {count} descripcions noves.",
                "type": "success",
                "sticky": False,
            },
        }

    def _get_base_path(self):
        ICP = self.env["ir.config_parameter"].sudo()
        return ICP.get_param("lensmemoriae.base_path", "/opt/odoo/custom/imatges")

    @api.depends("image_download_state")
    def _compute_download_progress(self):
        total = self.search_count([])
        if total:
            downloaded = self.search_count(
                [("image_download_state", "=", "downloaded")]
            )
            progress = (downloaded / total) * 100.0
        else:
            progress = 0.0
        for rec in self:
            rec.download_progress = progress

    @api.model
    def scan_directory(self):
        base = self._get_base_path()
        base_abs = os.path.abspath(base)
        if not os.path.isdir(base_abs):
            return 0
        allowed = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")
        created = 0
        for root, _dirs, files in os.walk(base_abs):
            for fname in files:
                if not fname.lower().endswith(allowed):
                    continue
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, base_abs)
                existing = self.search([("relpath", "=", rel)], limit=1)
                if existing:
                    continue
                try:
                    size = os.path.getsize(full)
                    mtime = datetime.fromtimestamp(os.path.getmtime(full))
                except Exception:
                    size = 0
                    mtime = fields.Datetime.now()
                mime, _ = mimetypes.guess_type(full)
                with open(full, "rb") as f:
                    image_data = base64.b64encode(f.read())
                self.sudo().create(
                    {
                        "name": fname,
                        "relpath": rel,
                        "file_size": size,
                        "mtime": mtime,
                        "mimetype": mime or "application/octet-stream",
                        "image": image_data,
                        "image_download_state": "downloaded",
                    }
                )
                created += 1
        return created

    @api.model
    def _download_image_from_api(self, record_id):
        record = self.browse(record_id)
        if not record or not record.codi_referencia:
            return
        if record.image_download_state == "downloaded":
            return
        record.write({"image_download_state": "downloading"})
        try:
            codi = record.codi_referencia
            api_url = (
                "https://backend.arxiusenlinia.cultura.gencat.cat"
                f"/unitat/objects?codiReferencia={codi}"
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            resp = requests.get(api_url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                item = data[0] if data else {}
            else:
                item = data
            download_url = item.get("downloadUrl")
            if not download_url:
                raise ValueError(f"No downloadUrl found for {codi}")
            img_resp = requests.get(download_url, headers=headers, timeout=120)
            img_resp.raise_for_status()
            image_data = base64.b64encode(img_resp.content)
            record.write(
                {
                    "image": image_data,
                    "image_download_state": "downloaded",
                    "mimetype": img_resp.headers.get("Content-Type", "image/jpeg"),
                }
            )
        except Exception:
            _logger.exception("Failed to download image for %s", codi)
            record.write({"image_download_state": "error"})

    @api.model
    def _cron_download_images(self, batch_size=5):
        pending = self.search(
            [("image_download_state", "=", "pending")], limit=batch_size
        )
        count = 0
        for rec in pending:
            self._download_image_from_api(rec.id)
            count += 1
        if count:
            _logger.info("Cron downloaded %d images", count)
        return count

    def action_download_pending(self):
        pending = self.search([("image_download_state", "=", "pending")])
        if not pending:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Info",
                    "message": "No hi ha imatges pendents de descarregar.",
                    "type": "info",
                    "sticky": False,
                },
            }
        count = 0
        for rec in pending:
            self._download_image_from_api(rec.id)
            count += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Downloads Processed",
                "message": f"S'han descarregat {count} imatges.",
                "type": "success",
                "sticky": False,
            },
        }

    def message_post(
        self,
        *,
        body="",
        message_type="notification",
        subtype_xmlid=None,
        subtype_id=False,
        **kwargs,
    ):
        message = super().message_post(
            body=body,
            message_type=message_type,
            subtype_xmlid=subtype_xmlid,
            subtype_id=subtype_id,
            **kwargs,
        )
        is_note = subtype_xmlid == "mail.mt_note"
        if not is_note and subtype_id:
            mt_note = self.env.ref("mail.mt_note")
            sid = (
                int(subtype_id)
                if not isinstance(subtype_id, models.Model)
                else subtype_id.id
            )
            is_note = sid == mt_note.id
        if (
            is_note
            and message
            and not self.env.user.has_group("lensmemoriae.group_moderator")
        ):
            message.sudo().moderation_state = "pending"
        return message

    def action_open_location_picker(self):
        self.ensure_one()
        ctx = dict(
            self.env.context,
            default_image_id=self.id,
            default_latitude=self.latitude,
            default_longitude=self.longitude,
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Set Location",
            "res_model": "lensmemoriae.location.picker",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def action_scan(self):
        base = self._get_base_path()
        base_abs = os.path.abspath(base)
        if not os.path.isdir(base_abs):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Directory Not Found",
                    "message": (
                        f"Configured path: {base}\nThe directory does not exist."
                    ),
                    "type": "danger",
                    "sticky": True,
                },
            }
        created = self.scan_directory()
        total = self.search_count([])
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Scan Complete",
                "message": (
                    f"Scanned: {base}\n"
                    f"New images: {created}\n"
                    f"Total in database: {total}"
                ),
                "type": "success" if created else "info",
                "next": {
                    "type": "ir.actions.act_window",
                    "res_model": "lensmemoriae.image",
                    "views": [[False, "list"], [False, "kanban"], [False, "form"]],
                    "target": "current",
                },
            },
        }

    def action_open_scrap_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Scrap XML Files",
            "res_model": "lensmemoriae.scrap.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def _xml_element_to_vals(self, el, fname):
        vals = {"name": fname}
        XML_TEXT_FIELDS = {
            "codi_grup",
            "arxiu",
            "codi_arxiu",
            "fons",
            "codi_fons",
            "tipus_unitat",
            "cod_unitat",
            "unitat_installacio",
            "nivell_descripcio",
            "cronologia",
            "data_inici",
            "continu_discontinu",
            "data_fi",
            "sense_data",
            "classificacio",
            "codi_classificacio",
            "procedencia",
            "codi_procedencia",
            "serie_cataleg",
            "codi_serie_cataleg",
            "expedient_inicial",
            "expedient_final",
            "observacions",
            "reportatge",
            "volum",
            "exemplars",
            "autoria",
            "onomastics",
            "toponimics",
            "llogaret",
            "lloc_precis",
            "municipi_longitud",
            "municipi_latitud",
            "llogaret_longitud",
            "llogaret_latitud",
            "tematics",
            "generes",
            "editors",
            "impremta",
            "diposit_legal",
            "codi_reprografia",
            "data_publicacio",
            "data_descarrega",
            "enllac_objecte_digital",
        }
        for child in el:
            tag = child.tag
            text = (child.text or "").strip()
            key = tag.replace("-", "_")
            if key == "titol_unitat_documental":
                vals["name"] = text if text else fname
            elif key == "descripcio":
                vals["description"] = text
                vals["xml_descripcio"] = text
                if text:
                    vals["description_approved"] = True
            elif key == "municipi_latitud" and text:
                try:
                    vals["latitude"] = float(text)
                except ValueError:
                    pass
            elif key == "municipi_longitud" and text:
                try:
                    vals["longitude"] = float(text)
                except ValueError:
                    pass
            elif tag == "codi_referencia":
                vals["codi_referencia"] = text
                vals["relpath"] = text
            elif key == "total_objectes_digitals" and text:
                try:
                    vals[key] = int(text)
                except ValueError:
                    vals[key] = text
            elif key in XML_TEXT_FIELDS:
                vals[key] = text
        return vals

    def action_scrap(self):
        source_path = "/opt/odoo/custom/source"
        source_abs = os.path.abspath(source_path)
        if not os.path.isdir(source_abs):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Directory Not Found",
                    "message": (
                        f"Configured path: {source_path}\nThe directory does not exist."
                    ),
                    "type": "danger",
                    "sticky": True,
                },
            }
        limit = self.env.context.get("scrap_limit", 0)
        filename_filter = self.env.context.get("scrap_filename_filter")
        processed = 0
        for root, _dirs, files in os.walk(source_abs):
            for fname in files:
                if not fname.lower().endswith(".xml"):
                    continue
                if filename_filter and filename_filter not in fname:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    tree = ET.parse(fpath)
                    xml_root = tree.getroot()
                    for el in xml_root.findall(".//element"):
                        vals = self._xml_element_to_vals(el, fname)
                        codi = vals.get("codi_referencia")
                        if not codi:
                            continue
                        existing = self.search(
                            [("codi_referencia", "=", codi)], limit=1
                        )
                        if existing:
                            existing.write(vals)
                        else:
                            self.create(vals)
                        processed += 1
                        if limit and processed >= limit:
                            break
                    if limit and processed >= limit:
                        break
                except Exception:
                    pass
                if limit and processed >= limit:
                    break
            if limit and processed >= limit:
                break
        msg = f"Processed {processed} elements."
        if limit:
            msg += f" (limit: {limit})"
        msg += " Image downloads have been queued."
        if not processed:
            msg = "No elements found to process."
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Scrap Complete",
                "message": msg,
                "type": "success" if processed else "info",
                "sticky": False,
            },
        }

    def action_clear_images(self):
        images = self.search([])
        count = len(images)
        messages = (
            self.env["mail.message"]
            .sudo()
            .search(
                [
                    ("model", "=", "lensmemoriae.image"),
                    ("res_id", "in", images.ids),
                ]
            )
        )
        msg_count = len(messages)
        messages.unlink()
        activities = (
            self.env["mail.activity"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "lensmemoriae.image"),
                    ("res_id", "in", images.ids),
                ]
            )
        )
        act_count = len(activities)
        activities.unlink()
        images.unlink()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("lensmemoriae.wordcloud_cache", False)
        ICP.set_param("lensmemoriae.wordcloud_last_computed", False)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Cleared",
                "message": (
                    f"Deleted {count} images, "
                    f"{msg_count} messages, "
                    f"and {act_count} activities."
                ),
                "type": "warning",
                "sticky": False,
            },
        }
