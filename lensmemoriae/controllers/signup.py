import json
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request


class LensMemoriaeSignup(http.Controller):
    MAX_ATTEMPTS = 3
    RATE_WINDOW = timedelta(hours=1)

    @http.route(
        "/lens-memoriae/signup",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def signup(self, **kwargs):
        if request.httprequest.method == "GET":
            return request.render("lensmemoriae.signup_form")

        # Honeypot: silently pretend success if bot filled hidden field
        if kwargs.get("website"):
            return request.redirect("/web/login?signup=ok")

        # Rate limiting
        ip = request.httprequest.remote_addr or "unknown"
        if not self._check_rate_limit(ip):
            return request.render(
                "lensmemoriae.signup_form",
                {
                    "errors": {"general": "Massa intents. Torna-ho a provar més tard."},
                },
            )

        login = kwargs.get("login", "").strip()
        name = kwargs.get("name", "").strip()
        password = kwargs.get("password", "")
        confirm_password = kwargs.get("confirm_password", "")

        errors = {}
        if not name:
            errors["name"] = "El nom és obligatori."
        if not login:
            errors["login"] = "El correu electrònic és obligatori."
        if not password:
            errors["password"] = "La contrasenya és obligatòria."
        if password != confirm_password:
            errors["confirm_password"] = "Les contrasenyes no coincideixen."

        if not errors:
            existing = (
                request.env["res.users"]
                .sudo()
                .search(["|", ("login", "=", login), ("email", "=", login)], limit=1)
            )
            if existing:
                errors["login"] = "Ja existeix un usuari amb aquest correu."

        if errors:
            return request.render(
                "lensmemoriae.signup_form",
                {
                    "errors": errors,
                    "name": name,
                    "login": login,
                },
            )

        try:
            request.env["res.users"].sudo().with_context(no_reset_password=True).create(
                {
                    "login": login,
                    "name": name,
                    "email": login,
                    "password": password,
                    "group_ids": [
                        (4, request.env.ref("base.group_user").id),
                    ],
                    "company_id": request.env.ref("base.main_company").id,
                    "company_ids": [(6, 0, [request.env.ref("base.main_company").id])],
                }
            )
        except Exception as e:
            return request.render(
                "lensmemoriae.signup_form",
                {
                    "errors": {"general": str(e)},
                    "name": name,
                    "login": login,
                },
            )

        request.session.authenticate(
            request.env,
            {"login": login, "password": password, "type": "password"},
        )

        return request.redirect("/web")

    @staticmethod
    def _check_rate_limit(ip):
        ICP = request.env["ir.config_parameter"].sudo()
        key = f"lensmemoriae.signup.ratelimit.{ip}"
        raw = ICP.get_param(key, "[]")
        now = datetime.utcnow()
        try:
            attempts = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            attempts = []
        cutoff = now - LensMemoriaeSignup.RATE_WINDOW
        attempts = [t for t in attempts if datetime.fromisoformat(t) > cutoff]
        if len(attempts) >= LensMemoriaeSignup.MAX_ATTEMPTS:
            return False
        attempts.append(now.isoformat())
        ICP.set_param(key, json.dumps(attempts))
        return True
