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
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    l10n_ar_afip_verification_type = fields.Selection(related='company_id.l10n_ar_afip_verification_type', readonly=False)

    l10n_ar_afip_fe_environment = fields.Selection(related='company_id.l10n_ar_afip_fe_environment', readonly=False)
    l10n_ar_afip_ws_key = fields.Binary(related='company_id.l10n_ar_afip_ws_key', readonly=False)
    l10n_ar_afip_ws_crt = fields.Binary(related='company_id.l10n_ar_afip_ws_crt', readonly=False)

    l10n_ar_afip_ws_key_fname = fields.Char('Private Key name', default='private_key.pem')
    l10n_ar_afip_ws_crt_fname = fields.Char(related='company_id.l10n_ar_afip_ws_crt_fname')

    def l10n_ar_action_create_certificate_request(self):
        self.ensure_one()
        if not self.company_id.partner_id.city:
            raise UserError(_('The company city must be defined before this action'))
        if not self.company_id.partner_id.country_id:
            raise UserError(_('The company country must be defined before this action'))
        if not self.company_id.partner_id.l10n_ar_vat:
            raise UserError(_('The company CUIT must be defined before this action'))
        return {'type': 'ir.actions.act_url', 'url': '/l10n_ar_afip_fe/download_afip_csr/' + str(self.company_id.id), 'target': 'new'}

    def l10n_ar_connection_test(self):
        self.ensure_one()
        error = ''
        if not self.l10n_ar_afip_ws_crt:
            error += '\n* ' + _('Please set a certificate in order to make the test')
        if not self.l10n_ar_afip_ws_key:
            error += '\n* ' + _('Please set a private key in order to make the test')
        if error:
            raise UserError(error)

        res = ''
        for webservice in ['wsfe', 'wsfex', 'wsbfe', 'wscdc']:
            try:
                self.company_id._l10n_ar_get_connection(webservice)
                res += ('\n* %s: ' + _('Connection is available')) % webservice
            except UserError as error:
                hint_msg = re.search('.*(HINT|CONSEJO): (.*)', error.name)
                msg = hint_msg.groups()[-1] if hint_msg and len(hint_msg.groups()) > 1 \
                    else '\n'.join(re.search('.*' + webservice + ': (.*)\n\n', error.name).groups())
                res += '\n* %s: ' % webservice + _('Connection failed') + '. %s' % msg.strip()
            except Exception as error:
                res += ('\n* %s: ' + _('Connection failed') + '. ' + _('This is what we get') + ' %s') % (webservice, repr(error))
        raise UserError(res)

    def random_demo_cert(self):
        self.company_id.set_demo_random_cert()
