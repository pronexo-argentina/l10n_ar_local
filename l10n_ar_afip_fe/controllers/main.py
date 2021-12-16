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
from odoo import http
from odoo.addons.web.controllers.main import content_disposition


class L10n_Ar_DownloadCertificateRequest(http.Controller):

    @http.route('/l10n_ar_afip_fe/download_afip_csr/<int:company_id>/', type='http', auth="user")
    def download_afip_csr(self, company_id, **kw):
        """ Download the certificate request file to upload in AFIP """
        company = http.request.env['res.company'].sudo().browse(company_id)
        content = company._l10n_ar_create_certificate_request()
        if not content:
            return http.request.not_found()
        return http.request.make_response(content, headers=[('Content-Type', 'text/plain'), ('Content-Disposition', content_disposition('request.csr'))])
