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
import logging

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    l10n_ar_afip_fe = fields.Selection(selection='_get_l10n_ar_afip_fe', compute='_compute_l10n_ar_afip_fe',
                                       string='AFIP FE')

    def _get_l10n_ar_afip_fe(self):
        return [('wsfe', _('Domestic market -without detail- RG2485 (WSFEv1)')),
                ('wsfex', _('Export -with detail- RG2758 (WSFEXv1)')),
                ('wsbfe', _('Fiscal Bond -with detail- RG2557 (WSBFE)'))]

    def _get_l10n_ar_afip_pos_types_selection(self):
        """ Add more options to the selection field AFIP POS System, re order options by common use """
        res = super()._get_l10n_ar_afip_pos_types_selection()
        res.insert(0, ('RAW_MAW', _('Electronic Invoice - Web Service')))
        res.insert(3, ('BFEWS', _('Electronic Fiscal Bond - Web Service')))
        res.insert(5, ('FEEWS', _('Export Voucher - Web Service')))
        return res

    @api.depends('l10n_ar_afip_pos_system')
    def _compute_l10n_ar_afip_fe(self):
        """ Depending on AFIP POS System selected set the proper AFIP FE """
        type_mapping = {'RAW_MAW': 'wsfe', 'FEEWS': 'wsfex', 'BFEWS': 'wsbfe'}
        for rec in self:
            rec.l10n_ar_afip_fe = type_mapping.get(rec.l10n_ar_afip_pos_system, False)

    def l10n_ar_check_afip_pos_number(self):
        """ Return information about the AFIP POS numbers related to the given AFIP FE """
        self.ensure_one()
        connection = self.company_id._l10n_ar_get_connection(self.l10n_ar_afip_fe)
        client, auth = connection._get_client()
        if self.company_id._get_environment_type() == 'testing':
            raise UserError(_('"Check Available AFIP PoS" is not implemented in testing mode for webservice %s', self.l10n_ar_afip_fe))
        if self.l10n_ar_afip_fe == 'wsfe':
            response = client.service.FEParamGetPtosVenta(auth)
        elif self.l10n_ar_afip_fe == 'wsfex':
            response = client.service.FEXGetPARAM_PtoVenta(auth)
        else:
            raise UserError(_('"Check Available AFIP PoS" is not implemented for webservice %s', self.l10n_ar_afip_fe))
        raise UserError(response)

    def _l10n_ar_get_afip_last_invoice_number(self, document_type):
        """ Consult via webservice the number of the last invoice register
        :return: integer with the last number register in AFIP for the given document type in this journals AFIP POS
        """
        self.ensure_one()
        pos_number = self.l10n_ar_afip_pos_number
        afip_fe = self.l10n_ar_afip_fe
        connection = self.company_id._l10n_ar_get_connection(afip_fe)
        client, auth = connection._get_client()
        last = errors = False

        # We need to call a different method for every webservice type and assemble the returned errors if they exist
        if afip_fe == 'wsfe':
            response = client.service.FECompUltimoAutorizado(auth, pos_number, document_type.code)
            if response.CbteNro:
                last = response.CbteNro
            if response.Errors:
                errors = response.Errors
        elif afip_fe == 'wsfex':
            data = auth.copy()
            data.update({'Cbte_Tipo': document_type.code, 'Pto_venta': pos_number})
            response = client.service.FEXGetLast_CMP(Auth=data)
            if response.FEXResult_LastCMP.Cbte_nro:
                last = response.FEXResult_LastCMP.Cbte_nro
            if response.FEXErr.ErrCode != 0 or response.FEXErr.ErrMsg != 'OK':
                errors = response.FEXErr
        elif afip_fe == 'wsbfe':
            data = auth.copy()
            data.update({'Tipo_cbte': document_type.code, 'Pto_venta': pos_number})
            response = client.service.BFEGetLast_CMP(Auth=data)
            if response.BFEResult_LastCMP.Cbte_nro:
                last = response.BFEResult_LastCMP.Cbte_nro
            if response.BFEErr.ErrCode != 0 or response.BFEErr.ErrMsg != 'OK':
                errors = response.BFEErr
        else:
            return(_('AFIP FE %s not implemented', afip_fe))

        if errors:
            raise UserError(_('We receive this error trying to consult the last invoice number to AFIP:\n%s', str(errors)))
        return last
