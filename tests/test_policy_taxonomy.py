import unittest

from danish_meat_tax.policy_taxonomy import classify_product


class PolicyTaxonomyTest(unittest.TestCase):
    def test_core_beef_and_pork_are_treated(self):
        self.assertEqual(classify_product("Hakket oksekoed 8-12%").treatment_group, "beef")
        self.assertEqual(classify_product("Svinekotelet").treatment_group, "pork")

    def test_lamb_is_livestock_exposed_not_control(self):
        assignment = classify_product("Lammekolle")
        self.assertTrue(assignment.treated)
        self.assertEqual(assignment.treatment_group, "lamb_sheep_goat")

    def test_poultry_is_food_control(self):
        assignment = classify_product("Kyllingebryst")
        self.assertFalse(assignment.treated)
        self.assertEqual(assignment.treatment_group, "control_poultry")
        self.assertEqual(assignment.analysis_role, "control_food")

    def test_dairy_is_livestock_exposed(self):
        assignment = classify_product("Letmaelk 1 liter")
        self.assertTrue(assignment.treated)
        self.assertEqual(assignment.treatment_group, "dairy_cattle")
        self.assertEqual(assignment.analysis_role, "treated_livestock_dairy")

    def test_fish_and_unknown_not_false_treated(self):
        self.assertFalse(classify_product("Torskefilet").treated)
        unknown = classify_product("Mystery product")
        self.assertEqual(unknown.treatment_group, "unknown")
        self.assertEqual(unknown.analysis_role, "exclude_unknown")

    def test_more_control_commodities_are_labeled(self):
        self.assertEqual(classify_product("Rugbroed").commodity, "grains_bread")
        self.assertEqual(classify_product("Bananer").commodity, "fruit_vegetables")

    def test_non_food_is_excluded(self):
        assignment = classify_product("Shampoo 250 ml")
        self.assertEqual(assignment.food_status, "non_food")
        self.assertEqual(assignment.analysis_role, "exclude_non_food")


if __name__ == "__main__":
    unittest.main()
