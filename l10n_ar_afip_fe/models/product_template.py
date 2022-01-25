##############################################################################
#
#    Copyright (C) 2007  pronexo.com  (https://www.pronexo.com)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError
import re


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    l10n_ar_ncm_code = fields.Char('NCM Code', copy=False, help='Code according to the Common Nomenclator of MERCOSUR')

    def _check_l10n_ar_ncm_code(self):
        self.ensure_one()
        if self.l10n_ar_ncm_code and not re.match('^[0-9\.]+$', self.l10n_ar_ncm_code):
            raise UserError(_(
                'it seems like the product "%s" has no valid NCM Code.\n\nPlease set a valid NCM code to continue.'
                ' You can go to AFIP page and review the list of available NCM codes', self.display_name))
