from odoo import models, fields, _
from odoo.exceptions import UserError
import zeep
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gross_income_type = fields.Selection([
        ('multilateral', 'Multilateral'),
        ('local', 'Local'),
        ('no_liquida', 'No Liquida'),
    ],
        'Gross Income Type',
    )
    gross_income_jurisdiction_ids = fields.Many2many(
        'res.country.state',
        string='Gross Income Jurisdictions',
        help='The state of the company is cosidered the main jurisdiction',
    )
    start_date = fields.Date(
        'Start-up Date',
    )
 
    estado_padron = fields.Char(
        'Estado AFIP',
    )
    imp_ganancias_padron = fields.Selection([
        ('NI', 'No Inscripto'),
        ('AC', 'Activo'),
        ('EX', 'Exento'),
        # ('NA', 'No alcanzado'),
        # ('XN', 'Exento no alcanzado'),
        # ('AN', 'Activo no alcanzado'),
        ('NC', 'No corresponde'),
    ],
        'Ganancias',
    )
    # vat_tax_type_padron = fields.Selection([
    imp_iva_padron = fields.Selection([
        ('NI', 'No Inscripto'),
        ('AC', 'Activo'),
        ('EX', 'Exento'),
        ('NA', 'No alcanzado'),
        ('XN', 'Exento no alcanzado'),
        ('AN', 'Activo no alcanzado'),
        # ('NC', 'No corresponde'),
    ],
        'IVA',
    )
    integrante_soc_padron = fields.Selection(
        [('N', 'No'), ('S', 'Si')],
        'Integrante Sociedad',
    )
    monotributo_padron = fields.Selection(
        [('N', 'No'), ('S', 'Si')],
        'Monotributo',
    )
    actividad_monotributo_padron = fields.Char(
    )
    empleador_padron = fields.Boolean(
    )
    """actividades_padron = fields.Many2many(
        'afip.activity',
        'res_partner_afip_activity_rel',
        'partner_id', 
        'afip_activity_id',
        'Actividades',
    )
    impuestos_padron = fields.Many2many(
        'afip.tax',
        'res_partner_afip_tax_rel',
        'partner_id', 'afip_tax_id',
        'Impuestos',
    )"""
    last_update_padron = fields.Date(
        'Last Update Padron',
    )

    def update_constancia_from_padron_afip(self):
        self.ensure_one()
        # TODO implementar, al 30.11.2017 solo ws_sr_padron_a4 esta
        # implementado
        return True
        # # DESACTIVAMOS ESTO HASTA ARREGLARLO
        # cuit = self.cuit
        # # cuit = self.cuit_required

        # # descarga de constancia
        # # basedir = os.path.join(os.getcwd(), 'cache')
        # # tmpfilename = os.path.join(basedir, "constancia.pdf")
        # tmpfilename = "/tmp/constancia.pdf"
        # # sie queremos mejora esto podriamos no hardecodearlo con esto
        # # https://bugs.launchpad.net/openobject-addons/+bug/1040901
        # padron = self.env.user.company_id.get_connection(
        #     'ws_sr_padron_a5').connect()
        # padron.DescargarConstancia(cuit, tmpfilename)
        # f = file(tmpfilename, 'r')
        # constancia = base64.b64decode(base64.encodestring(f.read()))
        # f.close()
        # attachments = [
        #     ('Constancia %s %s.pdf' % (
        #         self.name,
        #         fields.Date.context_today(self)),
        #         constancia)]
        # self.message_post(
        #     subject="Constancia de inscripción actualizada",
        #     # subject="Actualizacion de datos desde Padron AFIP",
        #     # body="Datos utilizados:<br/>%s" % vals,
        #     attachments=attachments)

    



    def get_data_from_padron_afip(self):
        self.ensure_one()
        vat = self.ensure_vat()

        # if there is certificate for current company use that one, if not use the company with first certificate found
        company = self.env.company if self.env.company.sudo().l10n_ar_afip_ws_crt else self.env['res.company'].search(
            [('l10n_ar_afip_ws_crt', '!=', False)], limit=1)
        if not company:
            raise UserError(_('Please configure an AFIP Certificate in order to continue'))
        client, auth = company._l10n_ar_get_connection('ws_sr_padron_a5')._get_client()

        error_msg = _(
            'No pudimos actualizar desde padron afip al partner %s (%s).\nRecomendamos verificar manualmente en la'
            ' página de AFIP.\nObtuvimos este error:\n%s')

        errors = []
        values = {}
        try:
            res = client.service.getPersona(
                sign=auth.get('Sign'), token=auth.get('Token'), cuitRepresentada=auth.get('Cuit'), idPersona=vat)

            if res.errorConstancia:
                errors.append(res.errorConstancia)
            if res.errorMonotributo:
                errors.append(res.errorMonotributo)
            if res.errorRegimenGeneral:
                errors.append(res.errorRegimenGeneral)
        except Exception as e:
            raise UserError(error_msg % (self.name, vat, e))

        if errors:
            raise UserError(error_msg % (self.name, vat, errors))

        data = zeep.helpers.serialize_object(res.datosGenerales, dict)
        if not data:
            raise UserError(error_msg % (self.name, vat, res))

        denominacion = data.get("razonSocial", "") or ", ".join([data.get("apellido", ""), data.get("nombre", "")])
        if not denominacion or denominacion == ', ':
            raise UserError(error_msg % (self.name, vat, 'La afip no devolvió nombre'))

        domicilio = data.get("domicilioFiscal", {})
        data_mt = zeep.helpers.serialize_object(res.datosMonotributo, dict) or {}
        data_rg = zeep.helpers.serialize_object(res.datosRegimenGeneral, dict) or {}
        impuestos = [imp["idImpuesto"]
                     for imp in data_mt.get("impuesto", []) + data_rg.get("impuesto", [])
                     if data.get('estadoClave') == 'ACTIVO']

        data_mt_actividades = data_mt.get("actividadMonotributista", []) or []
        if isinstance(data_mt_actividades, (dict,)):
            data_mt_actividades = [data_mt_actividades]

        actividades = [act["idActividad"]
                       for act in data_rg.get("actividad", []) + data_mt_actividades]
        cat_mt = data_mt.get("categoriaMonotributo", {})
        monotributo = "S" if cat_mt else "N"
        map_pronvincias = {
            0: 'CIUDAD AUTONOMA BUENOS AIRES', 1: 'BUENOS AIRES',
            2: 'CATAMARCA', 3: 'CORDOBA', 4: 'CORRIENTES', 5: 'ENTRE RIOS', 6: 'JUJUY',
            7: 'MENDOZA', 8: 'LA RIOJA', 9: 'SALTA', 10: 'SAN JUAN', 11: 'SAN LUIS',
            12: 'SANTA FE', 13: 'SANTIAGO DEL ESTERO', 14: 'TUCUMAN', 16: 'CHACO',
            17: 'CHUBUT', 18: 'FORMOSA', 19: 'MISIONES', 20: 'NEUQUEN', 21: 'LA PAMPA',
            22: 'RIO NEGRO', 23: 'SANTA CRUZ', 24: 'TIERRA DEL FUEGO'}
        provincia = map_pronvincias.get(domicilio.get("idProvincia"), "")

        if 32 in impuestos:
            imp_iva = "EX"
        elif 33 in impuestos:
            imp_iva = "NI"
        elif 34 in impuestos:
            imp_iva = "NA"
        else:
            imp_iva = "AC" if 30 in impuestos else "NI"

        values.update({
            'name': denominacion,
            'estado_padron': data.get('estadoClave'),
            'street': domicilio.get("direccion", domicilio.get("localidad", provincia)),
            'city': domicilio.get("localidad"),
            'zip': domicilio.get("codPostal", ""),
            #'actividades_padron': self.actividades_padron.search([('code', 'in', actividades)]).ids,
            #'impuestos_padron': self.impuestos_padron.search([('code', 'in', impuestos)]).ids,
            'imp_iva_padron': imp_iva,
            'monotributo_padron': monotributo,
            'actividad_monotributo_padron': cat_mt.get("descripcionCategoria") if cat_mt else "",
            'empleador_padron': True if 301 in impuestos else False,
            'integrante_soc_padron': "",
            'last_update_padron': fields.Date.today(),
        })

        ganancias_inscripto = [10, 11]
        ganancias_exento = [12]
        if set(ganancias_inscripto) & set(impuestos):
            values['imp_ganancias_padron'] = 'AC'
        elif set(ganancias_exento) & set(impuestos):
            values['imp_ganancias_padron'] = 'EX'
        elif monotributo == 'S':
            values['imp_ganancias_padron'] = 'NC'
        else:
            _logger.info("We couldn't get impuesto a las ganancias from padron, you must set it manually")

        if provincia:
            # depending on the database, caba can have one of this codes
            caba_codes = ['C', 'CABA', 'ABA']
            # if not localidad then it should be CABA.
            if not domicilio.get("localidad"):
                state = self.env['res.country.state'].search([
                    ('code', 'in', caba_codes), ('country_id.code', '=', 'AR')], limit=1)
            # If localidad cant be caba
            else:
                state = self.env['res.country.state'].search([
                    ('name', 'ilike', provincia), ('code', 'not in', caba_codes), ('country_id.code', '=', 'AR')],
                    limit=1)
            if state:
                values['state_id'] = state.id

        if imp_iva == 'NI' and monotributo == 'S':
            values['l10n_ar_afip_responsibility_type_id'] = self.env.ref('l10n_ar.res_RM').id
        elif imp_iva == 'AC':
            values['l10n_ar_afip_responsibility_type_id'] = self.env.ref('l10n_ar.res_IVARI').id
        elif imp_iva == 'EX':
            values['l10n_ar_afip_responsibility_type_id'] = self.env.ref('l10n_ar.res_IVAE').id
        else:
            _logger.info("We couldn't infer the AFIP responsability from padron, you must set it manually.")

        return values    




