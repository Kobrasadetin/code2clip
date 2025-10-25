
import types
import unittest

from extension_compute import compute_extension_filters


def _mk_settings(**overrides):
    settings = types.SimpleNamespace(
        extension_mode="categories",
        include_code=True,
        include_text=True,
        include_data=True,
        excluded_subsets={},
        included_extensions_text="",
        excluded_extensions_text="",
        custom_extensions_text="",
    )
    settings.__dict__.update(overrides)
    return settings


class TestExtensionCompute(unittest.TestCase):
    def test_categories_defaults_include_broadly(self):
        settings = _mk_settings()
        result = compute_extension_filters(settings)
        self.assertIn(".md", result)
        self.assertIn(".py", result)
        self.assertIn(".json", result)

    def test_allow_all_returns_empty_list(self):
        settings = _mk_settings(extension_mode="allow_all")
        self.assertEqual(compute_extension_filters(settings), [])

    def test_custom_mode_uses_exact_list_and_deny_list_applies(self):
        settings = _mk_settings(
            extension_mode="custom",
            custom_extensions_text="py, .md, .json",
            excluded_extensions_text=".md",
        )
        result = compute_extension_filters(settings)
        self.assertEqual(set(result), {".py", ".json"})

    def test_excluded_subset_is_removed(self):
        baseline = compute_extension_filters(_mk_settings())
        settings = _mk_settings(excluded_subsets={"Code": ["Code: Rust"]})
        filtered = compute_extension_filters(settings)
        self.assertIn(".rs", baseline)
        self.assertNotIn(".rs", filtered)

    def test_deny_list_has_last_precedence(self):
        settings = _mk_settings()
        self.assertIn(".json", compute_extension_filters(settings))
        settings.excluded_extensions_text = ".json"
        self.assertNotIn(".json", compute_extension_filters(settings))

    def test_categories_can_include_additional_extensions(self):
        settings = _mk_settings(included_extensions_text=".svg\n.blend")
        result = compute_extension_filters(settings)
        self.assertIn(".svg", result)
        self.assertIn(".blend", result)

    def test_custom_mode_accepts_newline_separated_extensions(self):
        settings = _mk_settings(
            extension_mode="custom",
            custom_extensions_text=".py\n.md\n.json",
        )
        result = compute_extension_filters(settings)
        self.assertEqual(set(result), {".py", ".md", ".json"})


if __name__ == "__main__":
    unittest.main()
