# Copyright 2004-2010 Tiny SPRL http://tiny.be
# Copyright 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# Copyright 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# Copyright  2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from random import randint

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


class ResPartnerIdCategory(models.Model):
    _name = "res.partner.id_category"
    _description = "Partner ID Category"
    _order = "name"

    def _get_default_color(self):
        return randint(1, 11)

    color = fields.Integer(string="Color Index", default=_get_default_color)
    code = fields.Char(
        required=True,
        help="Abbreviation or acronym of this ID type. For example, "
        "'driver_license'",
    )
    name = fields.Char(
        string="ID name",
        required=True,
        translate=True,
        help="Name of this ID type. For example, 'Driver License'",
    )
    active = fields.Boolean(default=True)
    validation_code = fields.Text(
        "Python validation code", help="Python code called to validate an id number."
    )

    @api.model
    def _search_duplicate(self, category_id, id_number, force_active=False):
        """Find duplicates for the given category and number."""
        domain = [
            ("category_id", "=", category_id),
            ("name", "=", id_number.name),
            ("name", "!=", False),
            ("id", "!=", id_number.id),
        ]

        if force_active:
            domain.append(("partner_id.active", "=", True))
        return self.env["res.partner.id_number"].search(domain)

    def _validation_eval_context(self, id_number):
        self.ensure_one()
        return {"self": self, "id_number": id_number}

    def validate_id_number(self, id_number):
        """Validate the given ID number
        The method raises an odoo.exceptions.ValidationError if the eval of
        python validation code fails
        """
        self.ensure_one()
        if self.env.context.get("id_no_validate") or not self.validation_code:
            return
        eval_context = self._validation_eval_context(id_number)
        try:
            safe_eval(self.validation_code, eval_context, mode="exec", nocopy=True)
        except Exception as e:
            raise UserError(
                self.env._(
                    "Error when evaluating the id_category "
                    "validation code: \n %(name)s \n(%(error)s)",
                    name=self.name,
                    error=e,
                )
            ) from e
        if eval_context.get("failed", False):
            raise ValidationError(
                self.env._(
                    "%(id_name)s is not a valid %(cat_name)s identifier",
                    id_name=id_number.name,
                    cat_name=self.name,
                )
            )
