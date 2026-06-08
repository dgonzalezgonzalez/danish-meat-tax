import unittest

from danish_meat_tax.policy_taxonomy import classify_product


class PolicyTaxonomyTest(unittest.TestCase):
    def test_core_beef_and_pork_are_treated(self):
        self.assertEqual(classify_product("Hakket oksekød 8-12%").treatment_group, "beef")
        self.assertEqual(classify_product("Svinekotelet").treatment_group, "pork")

    def test_lamb_is_livestock_exposed_not_control(self):
        assignment = classify_product("Lammekølle")
        self.assertTrue(assignment.treated)
        self.assertEqual(assignment.treatment_group, "lamb_sheep_goat")

    def test_poultry_is_sensitivity_group(self):
        assignment = classify_product("Kyllingebryst")
        self.assertTrue(assignment.treated)
        self.assertEqual(assignment.policy_confidence, "sensitivity")

    def test_fish_and_unknown_not_false_treated(self):
        self.assertFalse(classify_product("Torskefilet").treated)
        self.assertEqual(classify_product("Mystery product").treatment_group, "unknown")


if __name__ == "__main__":
    unittest.main()
