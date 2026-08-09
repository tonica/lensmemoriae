import base64
import csv
import io
import json
import logging
import re
import unicodedata
import uuid
import zipfile
from xml.sax.saxutils import escape as xml_escape

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

AENL_DEFAULT_API = "https://backend.arxiusenlinia.cultura.gencat.cat"
AENL_FRONT = "https://arxiusenlinia.cultura.gencat.cat"
AENL_DETAIL_UNITAT = "/cercaavancada/detallunitat/"
AENL_PAGE_SIZE = 1000
AENL_TIMEOUT = 120

_AENL_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

# XML tag mapping used by the web frontend when exporting units (formatarRegistre / RI).
AENL_XML_FIELD_MAP = {
    "codiGrup": "codi_grup",
    "nomArxiu": "arxiu",
    "arxiuNom": "arxiu",
    "codiArxiu": "codi_arxiu",
    "nomFons": "fons",
    "codiFons": "codi_fons",
    "tipusUnitat": "tipus_unitat",
    "codiUnitat": "cod_unitat",
    "codiReferencia": "codi_referencia",
    "unitatInstalacio": "unitat_installacio",
    "nivellDesc": "nivell_descripcio",
    "titol": "titol_unitat_documental",
    "cronologia": "cronologia",
    "dataIniciStr": "data_inici",
    "continu": "continu-discontinu",
    "dataFiStr": "data_fi",
    "senseDates": "sense_data",
    "classificacioDesc": "classificacio",
    "codiClassificacio": "codi_classificacio",
    "procedenciaDesc": "procedencia",
    "codiProcedencia": "codi_procedencia",
    "catalegSerieNom": "serie_cataleg",
    "codiSerie": "codi_serie_cataleg",
    "expInicial": "expedient_inicial",
    "expFinal": "expedient_final",
    "descripcioFull": "descripcio",
    "observacions": "observacions",
    "reportatgeNom": "reportatge",
    "volum": "volum",
    "exemplarsList": "exemplars",
    "autorsList": "autoria",
    "onomasticsList": "onomastics",
    "toponimicsList": "toponimics",
    "nomLlogaret": "llogaret",
    "llocPrecisList": "lloc_precis",
    "municipiLongitud": "municipi_longitud",
    "municipiLatitud": "municipi_latitud",
    "llogaretLongitud": "llogaret_longitud",
    "llogaretLatitud": "llogaret_latitud",
    "tematicsList": "tematics",
    "impremta": "impremta",
    "generesList": "generes",
    "editorsList": "editors",
    "dipositLegal": "diposit_legal",
    "totalObjDigitals": "total_objectes_digitals",
    "codisReprografia": "codi_reprografia",
    "nomTipusFons": "tipus_fons",
    "codiTipusFons": "codi_tipus_fons",
    "anyInici": "any_inici",
    "anyFi": "any_fi",
    "urlEstable": "enllac_objecte_digital",
    "dataPublicacio": "data_publicacio",
    "dataDescarrega": "data_descarrega",
}

# List fields that are joined with " / " in the web export.
AENL_ARRAY_FIELDS = {
    "exemplarsList",
    "autorsList",
    "onomasticsList",
    "toponimicsList",
    "llocPrecisList",
    "tematicsList",
    "generesList",
    "editorsList",
}

# System parameter that caches the full fond list returned by /options/fons.
AENL_FONS_CACHE_KEY = "lensmemoriae.aenl_fons_cache"


class LensMemoriaeArxiuFons(models.Model):
    _name = "lensmemoriae.arxiu.fons"
    _description = "Arxius en Línia - Fons descarregat"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Fons", required=True)
    codi_referencia = fields.Char(string="Codi de referència", required=True, index=True)
    codi_grup = fields.Char(string="Codi grup")
    codi_arxiu = fields.Integer(string="Codi arxiu")
    codi_fons = fields.Integer(string="Codi fons")
    arxiu_nom = fields.Char(string="Arxiu")
    centre = fields.Char(string="Centre")
    total_unitats = fields.Integer(string="Unitats documentals")
    state = fields.Selection(
        [("draft", "Esborrany"), ("processing", "Descarregant"), ("done", "Completat"), ("error", "Error")],
        string="Estat",
        default="draft",
        readonly=True,
    )
    error_message = fields.Text(string="Error", readonly=True)
    fetch_date = fields.Datetime(string="Data de descàrrega", readonly=True)
    serie_ids = fields.One2many("lensmemoriae.arxiu.serie", "fons_id", string="Sèries")
    csv_attachment_id = fields.Many2one("ir.attachment", string="Fitxer CSV", readonly=True)
    json_attachment_id = fields.Many2one("ir.attachment", string="Fitxer JSON", readonly=True)
    zip_attachment_id = fields.Many2one("ir.attachment", string="Fitxer ZIP", readonly=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        compute="_compute_attachment_ids",
        string="Fitxers",
        readonly=True,
    )

    @api.depends(
        "serie_ids.xml_attachment_id", "csv_attachment_id", "json_attachment_id", "zip_attachment_id"
    )
    def _compute_attachment_ids(self):
        for rec in self:
            ids = []
            if rec.csv_attachment_id:
                ids.append(rec.csv_attachment_id.id)
            if rec.json_attachment_id:
                ids.append(rec.json_attachment_id.id)
            if rec.zip_attachment_id:
                ids.append(rec.zip_attachment_id.id)
            for serie in rec.serie_ids:
                if serie.xml_attachment_id:
                    ids.append(serie.xml_attachment_id.id)
            rec.attachment_ids = [(6, 0, sorted(set(ids)))]

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    def action_download(self):
        self.ensure_one()
        if self.state == "processing":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": "La descàrrega del fons ja està en curs.",
                    "type": "warning",
                    "sticky": False,
                },
            }
        self.write({"state": "processing", "error_message": False})
        self.sudo().action_fetch_fons()
        return self._download_result_notification()

    def action_import_to_lensmemoriae(self):
        self.ensure_one()
        image = self.env["lensmemoriae.image"].sudo()
        processed = 0
        details = []
        batch_size = 500
        for serie in self.serie_ids:
            att = serie.xml_attachment_id
            if not att:
                continue
            content = att.raw
            if not content:
                continue
            n = image._process_scrap_xml(
                content, att.name or serie.name, 0, batch_size
            )
            processed += n
            details.append("%s: %d" % (serie.name, n))
        message = (
            "Importat del fons %s: %d elements." % (self.name, processed)
            if processed
            else "No s'ha pogut importar cap element (revisa els XML de les sèries)."
        )
        if details:
            message += " " + "; ".join(details)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "LensMemòria",
                "message": message,
                "type": "success" if processed else "warning",
                "sticky": False,
            },
        }

    def action_download_csv(self):
        self.ensure_one()
        return self._attachment_download_action(self.csv_attachment_id)

    def action_download_json(self):
        self.ensure_one()
        return self._attachment_download_action(self.json_attachment_id)

    def action_download_attachment(self, attachment_id):
        self.ensure_one()
        attachment = self.env["ir.attachment"].browse(attachment_id)
        return self._attachment_download_action(attachment)

    def action_download_zip(self):
        self.ensure_one()
        if not self.zip_attachment_id:
            attachments = self.attachment_ids
            if not attachments:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Arxius en Línia",
                        "message": "No hi ha fitxers generats per a aquest fons.",
                        "type": "warning",
                        "sticky": False,
                    },
                }
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for att in attachments.with_context(bin_size=False):
                    content = att.raw
                    if content is None:
                        content = base64.b64decode(att.datas or b"")
                    zf.writestr(att.name, content)
            zip_bytes = buffer.getvalue()
            self.write(
                {
                    "zip_attachment_id": self._create_attachment(
                        "%s.zip" % self._base_filename(),
                        zip_bytes,
                        "application/zip",
                        self._name,
                        self.id,
                    ).id,
                }
            )
        return self._attachment_download_action(self.zip_attachment_id)

    def _download_result_notification(self):
        self.ensure_one()
        if self.state == "done":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": (
                        "Fons descarregat: %d unitats i %d sèries. "
                        "Descarrega els fitxers des del registre del fons."
                    )
                    % (self.total_unitats, len(self.serie_ids)),
                    "type": "success",
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Arxius en Línia",
                "message": "Error en descarregar el fons: %s"
                % (self.error_message or "error desconegut"),
                "type": "danger",
            },
        }

    @api.model
    def _attachment_download_action(self, attachment):
        if not attachment:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Arxius en Línia",
                    "message": "El fitxer encara no s'ha generat.",
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=1" % attachment.id,
            "target": "self",
        }

    # ------------------------------------------------------------------
    # Fetch pipeline (runs in background job)
    # ------------------------------------------------------------------

    def action_fetch_fons(self):
        self.ensure_one()
        try:
            detail = self._fetch_fons_detail()
            if detail:
                self.write(
                    {
                        "codi_grup": detail.get("codiGrup") or self.codi_grup,
                        "codi_arxiu": detail.get("codiArxiu") or self.codi_arxiu,
                        "codi_fons": detail.get("codiFons") or self.codi_fons,
                        "arxiu_nom": detail.get("arxiuNom"),
                        "centre": detail.get("centre"),
                        "name": detail.get("nomFons") or self.name,
                    }
                )
            self._reset_files()

            tree = self._api_get(
                "/fons/tree",
                {"codiReferencia": self.codi_referencia, "ambTotals": "true"},
            )
            nodes = self._collect_tree_nodes(tree)

            all_records = []
            for node in nodes:
                records = self._fetch_units(node["codi"])
                if not records:
                    continue
                all_records.extend(records)
                xml_content = self._build_xml(records)
                filename = self._serie_filename(node)
                attachment = self._create_attachment(
                    filename,
                    xml_content,
                    "text/xml;charset=utf-8",
                    self._name,
                    self.id,
                )
                self.env["lensmemoriae.arxiu.serie"].create(
                    {
                        "fons_id": self.id,
                        "name": node["label"],
                        "codi_classificacio": node["codi"],
                        "unit_count": len(records),
                        "xml_attachment_id": attachment.id,
                    }
                )

            if all_records:
                self.write(
                    {
                        "csv_attachment_id": self._create_attachment(
                            self._base_filename() + ".csv",
                            self._build_csv(all_records),
                            "text/csv;charset=utf-8",
                            self._name,
                            self.id,
                        ).id,
                        "json_attachment_id": self._create_attachment(
                            self._base_filename() + ".json",
                            self._build_json(all_records),
                            "application/json;charset=utf-8",
                            self._name,
                            self.id,
                        ).id,
                    }
                )

            self.write(
                {
                    "state": "done",
                    "total_unitats": len(all_records),
                    "fetch_date": fields.Datetime.now(),
                    "error_message": False,
                }
            )
            _logger.info(
                "Fons %s (ref %s) descarregat: %d unitats, %d sèries",
                self.name,
                self.codi_referencia,
                len(all_records),
                len(self.serie_ids),
            )
        except Exception as exc:
            _logger.exception("Error descarregant el fons %s", self.codi_referencia)
            self.write({"state": "error", "error_message": str(exc)})
        return True

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _api_base(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("lensmemoriae.aenl_api_base", AENL_DEFAULT_API)
            or AENL_DEFAULT_API
        )

    def _api_get(self, path, params=None):
        resp = requests.get(
            self._api_base() + path,
            params=params,
            headers={"User-Agent": _AENL_UA, "Accept": "application/json"},
            timeout=AENL_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    @api.model
    def _api_search_fons(self, text):
        if not text:
            return []
        folded = self._fold_text(text)
        if not folded:
            return []
        return [
            item
            for item in self._get_fons_list()
            if folded in self._fold_text(item["label"])
        ][:50]

    @api.model
    def _fetch_fons_list(self):
        """Fetch the full fond list from the AENL API (autocomplete endpoint)."""
        data = self._api_get("/options/fons", {"text": "a"})
        if not isinstance(data, list):
            return []
        return [
            {"label": item.get("label") or "", "value": item.get("value") or ""}
            for item in data
            if item.get("value")
        ]

    @api.model
    def _get_fons_list(self):
        """Return the cached fond list, fetching and storing it when missing."""
        ICP = self.env["ir.config_parameter"].sudo()
        raw = ICP.get_param(AENL_FONS_CACHE_KEY)
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        items = self._fetch_fons_list()
        if items:
            ICP.set_param(AENL_FONS_CACHE_KEY, json.dumps(items))
        return items

    @api.model
    def action_refresh_fons_cache(self):
        items = self._fetch_fons_list()
        if items:
            self.env["ir.config_parameter"].sudo().set_param(
                AENL_FONS_CACHE_KEY, json.dumps(items)
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Llista de fons",
                "message": (
                    "Llista actualitzada: %d fons." % len(items)
                    if items
                    else "No s'ha pogut obtenir la llista de fons."
                ),
                "type": "success" if items else "warning",
                "sticky": False,
            },
        }

    @api.model
    def _fold_text(self, text):
        value = unicodedata.normalize("NFD", text or "")
        value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
        value = re.sub(r"[^A-Za-z0-9 ]", " ", value)
        return re.sub(r"\s+", " ", value).strip().lower()

    def _fetch_fons_detail(self):
        return self._api_get(
            "/fons/detail/full",
            {
                "codiReferencia": self.codi_referencia,
                "idSessio": str(uuid.uuid4()),
            },
        )

    def _fetch_units(self, codi_classificacio=None):
        params = self._search_params(codi_classificacio)
        records = []
        page = 1
        while True:
            data = self._api_get(
                "/unitat/search/advanced/export", dict(params, page=page)
            )
            if not isinstance(data, list) or not data:
                break
            records.extend(data)
            page += 1
            if len(data) < AENL_PAGE_SIZE:
                break
        return records

    def _search_params(self, codi_classificacio=None):
        params = {
            "selectedTipusCerca": "U",
            "buscarEnTitol": "true",
            "buscarEnDescripcio": "true",
            "buscarEnToponimic": "true",
            "buscarEnTematic": "true",
            "buscarEnOnomastic": "true",
            "centre": self.codi_grup,
            "tipusArxiu": "TOTS",
            "codiArxiu": self.codi_arxiu,
            "codiFons": self.codi_fons,
            "codiReferenciaFons": self.codi_referencia,
            "dataExtremaConcreta": "0",
            "mostrar": "TOTS",
            "classifDescendent": "false",
            "tipDocTextual": "true",
            "tipDocFotos": "true",
            "tipDocFotoDigital": "true",
            "tipDocFotoQuimica": "true",
            "tipDocPostal": "true",
            "tipDocProcFotomecanic": "true",
            "tipDocMapes": "true",
            "tipDocAudios": "true",
            "tipDocProdImpr": "true",
            "tipDocNomesMusicals": "false",
            "tipDocProdArt": "true",
            "fonsDocTextual": "true",
            "fonsDocNoTextual": "true",
        }
        if codi_classificacio:
            params["codiClassificacio"] = codi_classificacio
        return params

    @api.model
    def _collect_tree_nodes(self, node, out=None, root=True):
        if out is None:
            out = []
        if not root and node.get("data"):
            out.append(
                {
                    "label": self._clean_node_label(node.get("label") or node.get("data")),
                    "codi": node.get("data"),
                }
            )
        for child in node.get("children") or []:
            self._collect_tree_nodes(child, out, root=False)
        return out

    @api.model
    def _clean_node_label(self, label):
        value = re.sub(r"\s*\(\d+\)", "", label or "")
        value = re.sub(r"\s*\[\+\d+\]", "", value)
        return value.strip()

    # ------------------------------------------------------------------
    # File generation
    # ------------------------------------------------------------------

    @api.model
    def _format_value(self, key, value):
        if value is None:
            return ""
        if key in AENL_ARRAY_FIELDS and isinstance(value, list):
            return " / ".join(str(item) for item in value if item is not None)
        return str(value)

    @api.model
    def _normalise_record(self, record):
        record = dict(record)
        record.setdefault(
            "urlEstable",
            AENL_FRONT
            + AENL_DETAIL_UNITAT
            + (str(record.get("codiReferencia") or "")),
        )
        return record

    def _build_xml(self, records):
        lines = ['<?xml version="1.0"?>', "<elements>"]
        for record in records:
            record = self._normalise_record(record)
            lines.append("  <element>")
            for key, value in record.items():
                tag = AENL_XML_FIELD_MAP.get(key)
                if not tag:
                    continue
                text = xml_escape(self._format_value(key, value))
                lines.append("    <{tag}>{text}</{tag}>".format(tag=tag, text=text))
            lines.append("  </element>")
        lines.append("</elements>")
        return "\n".join(lines) + "\n"

    def _build_csv(self, records):
        if not records:
            return ""
        sample = self._normalise_record(records[0])
        columns = [
            AENL_XML_FIELD_MAP[key]
            for key in sample
            if AENL_XML_FIELD_MAP.get(key)
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for record in records:
            record = self._normalise_record(record)
            row = {}
            for key, value in record.items():
                tag = AENL_XML_FIELD_MAP.get(key)
                if not tag:
                    continue
                row[tag] = self._format_value(key, value)
            writer.writerow(row)
        return buffer.getvalue()

    @api.model
    def _build_json(self, records):
        return json.dumps(records, ensure_ascii=False, indent=2)

    def _create_attachment(self, name, content, mimetype, model, res_id):
        if isinstance(content, str):
            content = content.encode("utf-8")
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": base64.b64encode(content),
                "mimetype": mimetype,
                "res_model": model,
                "res_id": res_id,
            }
        )

    def _reset_files(self):
        old_attachments = self.env["ir.attachment"]
        old_attachments |= self.csv_attachment_id
        old_attachments |= self.json_attachment_id
        old_attachments |= self.zip_attachment_id
        for serie in self.serie_ids:
            if serie.xml_attachment_id:
                old_attachments |= serie.xml_attachment_id
        self.serie_ids.unlink()
        self.write(
            {
                "csv_attachment_id": False,
                "json_attachment_id": False,
                "zip_attachment_id": False,
            }
        )
        old_attachments.unlink()

    @api.model
    def _slugify(self, text):
        value = re.sub(r"\s+", "_", text or "").strip("_")
        value = re.sub(r"[^\w\-]", "", value, flags=re.UNICODE)
        return value or "serie"

    def _base_filename(self):
        return re.sub(r"[^\w\-.]", "_", self.codi_referencia)

    def _serie_filename(self, node):
        code = node.get("codi") or "sense_serie"
        slug = self._slugify(node.get("label"))
        return "{base}_{code}_{slug}.xml".format(
            base=self._base_filename(), code=code, slug=slug
        )
