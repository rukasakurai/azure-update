import importlib.util
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_script(module_name, filename):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


get_updates = load_script("get_azure_update", "1_get_azure_update.py")

os.environ.setdefault(
    "AZURE_OPENAI_ENDPOINT",
    "https://example.services.ai.azure.com/",
)
os.environ.setdefault("MODEL_DEPLOYMENT_NAME", "test-deployment")
make_pptx = load_script("make_jp_update_pptx", "2_make_jp_update_pptx.py")


def make_item(title, status=None, rings=None, tags=None, item_id="123"):
    return {
        "id": item_id,
        "title": title,
        "status": status,
        "availabilities": [{"ring": ring} for ring in (rings or [])],
        "tags": tags or [],
    }


class NormalizeUpdateStatusTests(unittest.TestCase):
    def test_status_resolution_cases(self):
        cases = [
            (
                "consistent general availability",
                make_item(
                    "Generally Available: Feature",
                    "Launched",
                    ["General Availability"],
                ),
                "一般提供",
                "Feature",
                None,
            ),
            (
                "preview prefix conflicts with launched status",
                make_item("Public Preview: Feature", "Launched", ["Preview"]),
                "要確認",
                "Feature",
                "title prefix and API status disagree",
            ),
            (
                "preview prefix conflicts with GA availability",
                make_item(
                    "Public Preview: Feature",
                    "In preview",
                    ["General Availability"],
                ),
                "要確認",
                "Feature",
                "title prefix and availability disagree",
            ),
            (
                "public preview prefix conflicts with private-only availability",
                make_item(
                    "Public Preview: Feature",
                    "In preview",
                    ["Private Preview"],
                ),
                "要確認",
                "Feature",
                "title prefix and availability disagree",
            ),
            (
                "corroborated GA announcement",
                make_item(
                    "Announcing: Feature",
                    "Launched",
                    ["General Availability"],
                    ["Announcement"],
                ),
                "一般提供",
                "Feature",
                None,
            ),
            (
                "announcement without lifecycle",
                make_item(
                    "Announcing: Feature",
                    rings=["Effective"],
                    tags=["Announcement"],
                ),
                "要確認",
                "Feature",
                "announcement lifecycle is not corroborated",
            ),
            (
                "private preview prefix",
                make_item(
                    "Private Preview: Feature",
                    "In preview",
                    ["Private Preview"],
                ),
                "プライベートプレビュー",
                "Feature",
                None,
            ),
            (
                "private preview ring refines broad status",
                make_item("Feature", "In preview", ["Private Preview"]),
                "プライベートプレビュー",
                "Feature",
                None,
            ),
            (
                "retirement ring",
                make_item(
                    "Feature retirement notice",
                    rings=["Retirement"],
                    tags=["Retirements"],
                ),
                "リタイアメント",
                "Feature retirement notice",
                None,
            ),
            (
                "retirement tag does not override public preview",
                make_item(
                    "Public Preview: Feature",
                    "In preview",
                    ["Preview"],
                    ["Retirements"],
                ),
                "パブリックプレビュー",
                "Feature",
                None,
            ),
            (
                "retirement tag is fallback evidence",
                make_item(
                    "Feature retirement notice",
                    tags=["Retirements"],
                ),
                "リタイアメント",
                "Feature retirement notice",
                None,
            ),
        ]

        for name, item, category, title, review_reason in cases:
            with self.subTest(name=name):
                result = get_updates.normalize_update_status(item)
                self.assertEqual(category, result["category"])
                self.assertEqual(title, result["title"])
                if review_reason:
                    self.assertEqual(review_reason, result["review"]["reason"])
                else:
                    self.assertIsNone(result["review"])

    def test_announcing_prefix_is_removed_from_display_title(self):
        title, prefix, label = get_updates.extract_title_signals(
            "Announcing: Feature"
        )

        self.assertEqual("Feature", title)
        self.assertEqual("Announcing", prefix)
        self.assertIsNone(label)

    def test_review_comment_contains_source_signals(self):
        result = get_updates.normalize_update_status(
            make_item(
                "Announcing: Feature",
                rings=["Effective"],
                tags=["Announcement"],
                item_id="567",
            )
        )

        comment = get_updates.format_status_review(result["review"])
        self.assertIn("<!-- status-review", comment)
        self.assertIn("availability: Effective", comment)
        self.assertIn("id: 567", comment)


class PowerPointTitleTests(unittest.TestCase):
    def test_category_is_removed_from_model_prompt_and_reattached(self):
        slide_text = """# 一般提供: Announcing: Feature

<!-- status-review
reason: example
-->

## 更新対象機能
Azure Example
"""

        category, prompt = make_pptx.prepare_slide_prompt(slide_text)

        self.assertEqual("一般提供", category)
        self.assertTrue(prompt.startswith("# Announcing: Feature"))
        self.assertNotIn("status-review", prompt)
        self.assertEqual(
            "一般提供: 翻訳済み機能",
            make_pptx.format_slide_title(category, "翻訳済み機能"),
        )


if __name__ == "__main__":
    unittest.main()
