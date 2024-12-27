# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class SomethingCase(TransactionCase):
    def setUp(cls):
        super().setUp()

        cls.product_tmpl = cls.env["product.template"].create({"name": "Test Template"})
        cls.product_var_1 = cls.env["product.product"].create(
            {"name": "Test Variant 1", "product_tmpl_id": cls.product_tmpl.id}
        )
        cls.product_var_2 = cls.env["product.product"].create(
            {"name": "Test Variant 2", "product_tmpl_id": cls.product_tmpl.id}
        )
        cls.doc1 = cls.env["product.document"].create(
            {
                "name": "Test Document 1",
                "type": "url",
                "url": "https://www.test.com/",
                "res_model": cls.product_tmpl._name,
                "res_id": cls.product_tmpl.id,
            }
        )
        cls.doc2 = cls.env["product.document"].create(
            {
                "name": "Test Document 2",
                "type": "url",
                "url": "https://www.test.com/",
                "res_model": cls.product_var_1._name,
                "res_id": cls.product_var_1.id,
            }
        )

    def test_document_counts(self):
        self.assertEqual(self.product_tmpl.product_document_count, 1)
        self.assertEqual(self.product_var_1.product_document_count, 2)
        self.assertEqual(self.product_var_2.product_document_count, 1)

    def test_product_action_open_documents(self):
        """Test the document action for product variants"""
        action = self.product_var_1.action_open_documents()
        self.assertEqual(
            action["context"]["default_parent_res_id"], self.product_tmpl.id
        )
        self.assertFalse(action["context"]["search_default_context_variant"])
        self.assertFalse(action["context"]["search_default_context_template"])
        self.assertTrue(action["context"]["search_default_context_variant_template"])

    def test_template_action_open_documents(self):
        """Test the document action for product template"""
        action = self.product_tmpl.action_open_documents()
        self.assertTrue(action["context"]["search_default_context_template"])
