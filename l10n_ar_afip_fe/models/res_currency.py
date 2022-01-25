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
from odoo import models, _
from odoo.exceptions import UserError
import datetime
from odoo.tools import format_date


class ResCurrency(models.Model):

    _inherit = "res.currency"

    def l10n_ar_action_get_afip_fe_currency_rate(self):
        date, rate = self._l10n_ar_get_afip_fe_currency_rate()
        date = format_date(self.env, datetime.datetime.strptime(date, '%Y%m%d'), date_format='EEEE, dd MMMM YYYY')
        raise UserError(_('Last Business Day') + ': %s' % date + '\n' + _('Rate:') + ' %s' % rate)

    def _l10n_ar_get_afip_fe_currency_rate(self, afip_fe='wsfe'):
        """ Return the date and rate for a given currency
        This is only for the user so that he can quickly check the last rate on afip por a currency.
        This is really useful. There is a NTH for the future to integrate this with the automtaic currency rates """
        self.ensure_one()
        if not self.l10n_ar_afip_code:
            raise UserError(_('No AFIP code for currency %s. Please configure the AFIP code consulting information in AFIP page', self.name))
        if self.l10n_ar_afip_code == 'PES':
            raise UserError(_('No rate for ARS (is the base currency for AFIP)'))

        connection = self.env.company._l10n_ar_get_connection(afip_fe)
        client, auth = connection._get_client()
        if afip_fe == 'wsfe':
            response = client.service.FEParamGetCotizacion(auth, MonId=self.l10n_ar_afip_code)
            if response.Errors:
                raise UserError(_('The was an error obtaining the rate:\n\n * Code %s -  %s') % (response.Errors.Err[0].Code, response.Errors.Err[0].Msg))
            # Events None
            date = response.ResultGet.FchCotiz
            rate = response.ResultGet.MonCotiz
        elif afip_fe == 'wsfex':
            response = client.service.FEXGetPARAM_Ctz(auth, Mon_id=self.l10n_ar_afip_code)
            date = response.FEXResultGet.Mon_fecha
            rate = response.FEXResultGet.Mon_ctz
        else:
            raise UserError(_('Get AFIP currency rate not implemented for webservice %s', afip_fe))
        return date, rate
