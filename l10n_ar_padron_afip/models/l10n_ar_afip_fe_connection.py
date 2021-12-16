# Part of Odoo. See LICENSE file for full copyright and licensing details.
#from odoo import fields, models, api, _
from odoo import models, api, _



class L10nArAfip_feConnection(models.Model):

    _inherit = "l10n_ar.afip_fe.connection"


    def _get_l10n_ar_afip_fe(self):
        """ Return the list of values of the selection field. """
        res = super()._get_l10n_ar_afip_fe()
        return [('ws_sr_padron_a5', _('Servicio de Consulta de Padrón Alcance 5'))] + res

    @api.model
    def _l10n_ar_get_afip_fe_url(self, afip_fe, environment_type):
        """ extend to add ws_sr_padron_a5 webservice """
        res = super()._l10n_ar_get_afip_fe_url(afip_fe, environment_type)
        if res:
            return res

        ws_data = {
            'ws_sr_padron_a5': {
                'production': 'https://aws.afip.gov.ar/sr-padron/webservices/personaServiceA5?wsdl',
                'testing': 'https://awshomo.afip.gov.ar/sr-padron/webservices/personaServiceA5?wsdl',
        }}
        return ws_data.get(afip_fe, {}).get(environment_type)
