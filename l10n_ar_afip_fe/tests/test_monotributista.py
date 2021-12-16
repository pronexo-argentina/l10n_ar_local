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
from odoo.tests import tagged
from . import common
import logging

_logger = logging.getLogger(__name__)


class TestMono(common.TestEdi):

    @classmethod
    def setUpClass(cls):
        # Issue ['C', 'E'] and  Receive ['B', 'C', 'I']
        super(TestMono, cls).setUpClass()
        cls.company_mono = cls.env.ref('l10n_ar.company_mono')
        context = dict(cls.env.context, allowed_company_ids=[cls.company_mono.id])
        cls._create_afip_connections(cls, cls.company_mono)
        cls.env = cls.env(context=context)


@tagged('fe', 'mono')
class TestFE(TestMono):

    @classmethod
    def setUpClass(cls):
        super(TestFE, cls).setUpClass()
        cls.partner = cls.partner_ri
        cls.journal = cls._create_journal(cls, 'wsfe')
        cls.document_type.update({
            'invoice_c': cls.env.ref('l10n_ar.dc_c_f'),
            'debit_note_c': cls.env.ref('l10n_ar.dc_c_nd'),
            'credit_note_c': cls.env.ref('l10n_ar.dc_c_nc'),
            'invoice_mipyme_c': cls.env.ref('l10n_ar.dc_fce_c_f')})

    def test_00_connection(self):
        self._test_connection()

    def test_01_consult_invoice(self):
        self._test_consult_invoice()

    def test_02_invoice_c_product(self):
        self._test_case('invoice_c', 'product')

    def test_03_invoice_c_service(self):
        self._test_case('invoice_c', 'service')

    def test_04_invoice_c_product_service(self):
        self._test_case('invoice_c', 'product_service')

    def test_05_debit_note_c_product(self):
        invoice = self._test_case('invoice_c', 'product')
        self._test_case_debit_note('debit_note_c', invoice)

    def test_06_debit_note_c_service(self):
        invoice = self._test_case('invoice_c', 'service')
        self._test_case_debit_note('debit_note_c', invoice)

    def test_06_debit_note_c_product_service(self):
        invoice = self._test_case('invoice_c', 'product_service')
        self._test_case_debit_note('debit_note_c', invoice)

    def test_07_credit_note_c_product(self):
        invoice = self._test_case('invoice_c', 'product')
        self._test_case_credit_note('credit_note_c', invoice)

    def test_08_credit_note_c_service(self):
        invoice = self._test_case('invoice_c', 'service')
        self._test_case_credit_note('credit_note_c', invoice)

    def test_09_credit_note_c_product_service(self):
        invoice = self._test_case('invoice_c', 'product_service')
        self._test_case_credit_note('credit_note_c', invoice)

    def test_10_invoice_mipyme_c_product(self):
        self._test_case('invoice_mipyme_c', 'product')

    def test_11_invoice_mipyme_c_service(self):
        self._test_case('invoice_mipyme_c', 'service')

    def test_12_invoice_mipyme_c_product_service(self):
        self._test_case('invoice_mipyme_c', 'product_service')


@tagged('fex', 'mono')
class TestFEX(common.TestFex, TestMono):

    def test_01_invoice_e_product(self):
        self._test_case('invoice_e', 'product')

    def test_02_invoice_e_service(self):
        self._test_case('invoice_e', 'service')

    def test_03_invoice_e_product_service(self):
        self._test_case('invoice_e', 'product_service')
