import os
import unittest


class TestFrontendFiles(unittest.TestCase):

    def test_required_frontend_files_exist(self):
        required_files = [
            "frontend/index.html",
            "frontend/pages/login.html",
            "frontend/pages/signup.html",
            "frontend/css/style.css",
            "frontend/js/app.js",
        ]

        for file_path in required_files:
            with self.subTest(file=file_path):
                self.assertTrue(
                    os.path.isfile(file_path),
                    f"Required frontend file is missing: {file_path}"
                )

    def test_homepage_contains_finaltake_brand(self):
        with open("frontend/index.html", "r", encoding="utf-8") as file:
            content = file.read()

        self.assertIn("FinalTake", content)

    def test_login_page_contains_form(self):
        with open("frontend/pages/login.html", "r", encoding="utf-8") as file:
            content = file.read().lower()

        self.assertIn("<form", content)

    def test_signup_page_contains_form(self):
        with open("frontend/pages/signup.html", "r", encoding="utf-8") as file:
            content = file.read().lower()

        self.assertIn("<form", content)


if __name__ == "__main__":
    unittest.main()