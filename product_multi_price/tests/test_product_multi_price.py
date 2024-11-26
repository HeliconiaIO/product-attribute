# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestProductMultiPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.price_name_obj = cls.env["product.multi.price.name"]
        cls.price_field_1 = cls.price_name_obj.create({"name": "test_field_1"})
        cls.price_field_2 = cls.price_name_obj.create({"name": "test_field_2"})
        prod_tmpl_obj = cls.env["product.template"]
        prod_prod_obj = cls.env["product.product"]
        cls.prod_1 = prod_tmpl_obj.create(
            {
                "name": "Test Product Template",
                "price_ids": [
                    (0, 0, {"name": cls.price_field_1.id, "price": 5.5}),
                    (0, 0, {"name": cls.price_field_2.id, "price": 20.0}),
                ],
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )

        cls.prod_prod = prod_prod_obj.create(
            {
                "name": "Test Product Product",
                "price_ids": [
                    (0, 0, {"name": cls.price_field_1.id, "price": 5.5}),
                    (0, 0, {"name": cls.price_field_2.id, "price": 20.0}),
                ],
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )

        cls.prod_att_1 = cls.env["product.attribute"].create({"name": "Color"})
        cls.prod_attr1_v1 = cls.env["product.attribute.value"].create(
            {"name": "red", "attribute_id": cls.prod_att_1.id}
        )
        cls.prod_attr1_v2 = cls.env["product.attribute.value"].create(
            {"name": "blue", "attribute_id": cls.prod_att_1.id}
        )
        cls.prod_2 = prod_tmpl_obj.create(
            {
                "name": "Test Product 2 With Variants",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.prod_att_1.id,
                            "value_ids": [
                                (6, 0, [cls.prod_attr1_v1.id, cls.prod_attr1_v2.id])
                            ],
                        },
                    )
                ],
            }
        )
        cls.prod_prod_2_1 = cls.prod_2.product_variant_ids[0]
        cls.prod_prod_2_2 = cls.prod_2.product_variant_ids[1]
        cls.prod_prod_2_1.write(
            {
                "price_ids": [
                    (0, 0, {"name": cls.price_field_1.id, "price": 6.6}),
                    (0, 0, {"name": cls.price_field_2.id, "price": 7.7}),
                ],
            }
        )
        cls.prod_prod_2_2.write(
            {
                "price_ids": [
                    (0, 0, {"name": cls.price_field_1.id, "price": 8.8}),
                    (0, 0, {"name": cls.price_field_2.id, "price": 9.9}),
                ],
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "compute_price": "formula",
                            "base": "multi_price",
                            "multi_price_name": cls.price_field_1.id,
                            "price_discount": 10,
                            "applied_on": "3_global",
                        },
                    )
                ],
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 10.0,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,  # default UOM
                "uom_po_id": cls.env.ref("uom.product_uom_unit").id,  # purchase UOM
            }
        )
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")  # another UOM (e.g., kilogram)

    def test_product_multi_price_pricelist(self):
        """Pricelists based on multi prices for templates or variants"""

        # Testing template prices
        price = self.pricelist.with_context(
            pricelist=self.pricelist.id
        )._get_products_price(self.prod_1, 1)
        self.assertAlmostEqual(price.get(self.prod_1.id), 4.95)

        # Testing variant 1 prices
        price = self.pricelist.with_context(
            pricelist=self.pricelist.id
        )._get_products_price(self.prod_prod_2_1, 1)
        self.assertAlmostEqual(price.get(self.prod_prod_2_1.id), 5.94)

        # Testing variant 2 prices
        price = self.pricelist.with_context(
            pricelist=self.pricelist.id
        )._get_products_price(self.prod_prod_2_2, 1)
        self.assertAlmostEqual(price.get(self.prod_prod_2_2.id), 7.92)

        # Additional coverage: check price fields after creation
        self.assertEqual(len(self.prod_1.price_ids), 2)
        self.assertEqual(self.prod_1.price_ids[0].name.id, self.price_field_1.id)
        self.assertEqual(self.prod_1.price_ids[1].name.id, self.price_field_2.id)

        # Ensure price is set correctly for variants
        self.assertEqual(len(self.prod_prod_2_1.price_ids), 2)
        self.assertEqual(self.prod_prod_2_1.price_ids[0].name.id, self.price_field_1.id)
        self.assertEqual(self.prod_prod_2_1.price_ids[1].name.id, self.price_field_2.id)

        self.assertEqual(len(self.prod_prod_2_2.price_ids), 2)
        self.assertEqual(self.prod_prod_2_2.price_ids[0].name.id, self.price_field_1.id)
        self.assertEqual(self.prod_prod_2_2.price_ids[1].name.id, self.price_field_2.id)

        # Testing edge case: empty pricelist
        empty_pricelist = self.env["product.pricelist"].create(
            {"name": "Empty Pricelist"}
        )
        price = empty_pricelist._get_products_price(self.prod_1, 1)
        self.assertEqual(price.get(self.prod_1.id), 1.0)

    def test_get_views_with_group(self):
        """Test get_views method with group membership"""

        # Simulate user with the group
        group = self.env.ref("product_multi_price.group_show_multi_prices")
        user_with_group = self.env["res.users"].create(
            {
                "name": "User with Group",
                "login": "user_with_group",
                "groups_id": [(4, group.id)],
            }
        )

        user_without_group = self.env["res.users"].create(
            {
                "name": "User without Group",
                "login": "user_without_group",
                "groups_id": [(3, group.id)],
            }
        )
        # Check views as a user with the group
        self.env["ir.model.data"].clear_caches()
        self.prod_1.with_user(user_with_group).get_views([], {})
        # Check views as a user without the group
        self.env["ir.model.data"].clear_caches()
        views_without_group = self.prod_1.with_user(user_without_group).get_views(
            [], {}
        )
        self.assertNotIn(
            "group_show_multi_prices",
            str(views_without_group),
            f"Unexpected 'group_show_multi_prices' in {views_without_group}",
        )

    def test_convert_to_price_uom_with_context(self):
        """Test price conversion with a specific context"""
        # Add the context to the environment
        env_with_uom = self.env["product.product"].with_context(uom=self.uom_kg.id)

        # Fetch the product in the updated environment
        product = env_with_uom.browse(self.prod_prod.id)
        test_price = 100.0
        # Perform the operation
        result = product._convert_to_price_uom(test_price)

        expected_result = 100.0
        self.assertEqual(
            result, expected_result, "The price conversion did not work as expected"
        )

    def test_convert_to_price_uom_without_context(self):
        """Test _convert_to_price_uom without 'uom' in the context"""
        price = 10.0  # base price in product's default UOM
        # No context for 'uom', so it should use the default UOM
        converted_price = self.product._convert_to_price_uom(price)
        self.assertTrue(
            converted_price > 0, "The converted price should be greater than 0"
        )

    def test_convert_to_price_uom_default_uom(self):
        """Test _convert_to_price_uom when context is not set and UOM is default"""
        price = 10.0  # base price in product's default UOM
        # Check if the price is converted correctly when default UOM is used
        converted_price = self.product._convert_to_price_uom(price)
        self.assertTrue(
            converted_price > 0, "The converted price should be greater than 0"
        )

    def test_get_multiprice_pricelist_price(self):
        """Test the logic for getting price based on multi-price pricelist."""

        # Test without discount, surcharge, margin
        rule = self.env["product.pricelist.item"].create(
            {
                "compute_price": "formula",
                "base": "multi_price",
                "multi_price_name": self.price_field_1.id,
                "price_discount": 0,
                "price_surcharge": 0,
                "price_min_margin": 0,
                "price_max_margin": 0,
                "applied_on": "3_global",
            }
        )
        price = self.prod_1._get_multiprice_pricelist_price(rule)
        self.assertEqual(price, 5.5, "The price should match the base price")

        # Test with a discount
        rule.price_discount = 10
        price = self.prod_1._get_multiprice_pricelist_price(rule)
        self.assertEqual(price, 4.95, "The price should be discounted by 10%")

        # Test with a surcharge
        rule.price_surcharge = 1.0
        price = self.prod_1._get_multiprice_pricelist_price(rule)
        self.assertEqual(price, 5.95, "The price should include the surcharge")

        # Test with min margin and max margin
        rule.price_max_margin = 1.0  # Set max margin
        rule.price_min_margin = 0.5  # Set min margin to be less than max margin
        price = self.prod_1._get_multiprice_pricelist_price(rule)
        self.assertGreater(price, 5.95, "The price should respect the min margin")
        self.assertLess(price, 6.95, "The price should respect the max margin")

    def test_get_views_with_group_1(self):
        """Test get_views method with group membership for context-based view filtering."""

        # Correctly reference the group by using self.env.ref
        group_show_multi_prices = self.env.ref(
            "product_multi_price.group_show_multi_prices"
        )

        # Create a user with the 'product_multi_price.group_show_multi_prices' group
        user_with_group = self.env["res.users"].create(
            {
                "name": "User with Group",
                "login": "user_with_group",
                "groups_id": [(4, group_show_multi_prices.id)],
            }
        )

        # Create a user without the group
        user_without_group = self.env["res.users"].create(
            {
                "name": "User without Group",
                "login": "user_without_group",
                "groups_id": [(3, group_show_multi_prices.id)],
            }
        )

        # Simulate the behavior for a user with the group
        self.prod_prod.with_user(user_with_group).get_views([], {})

        # Simulate the behavior for a user without the group
        views_without_group = self.prod_prod.with_user(user_without_group).get_views(
            [], {}
        )

        # Ensure that the context is not included for a user without the group
        self.assertNotIn(
            "group_show_multi_prices",
            str(views_without_group),
            "Unexpected context with 'group_show_multi_prices' for a user without the group.",
        )
