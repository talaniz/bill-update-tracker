import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]


class MothershipAssetTest(unittest.TestCase):
    def test_landing_page_links_to_known_local_services(self):
        landing = (PROJECT_ROOT / "landing/index.html").read_text()

        self.assertIn('href="http://deathstar.local:5678/"', landing)
        self.assertIn('href="/bill-update-tracker/"', landing)
        self.assertIn('href="/assets/pico.min.css"', landing)
        self.assertTrue((PROJECT_ROOT / "landing/assets/pico.min.css").is_file())

    def test_alloy_uses_only_approved_deployment_labels(self):
        config = (PROJECT_ROOT / "alloy/config.alloy").read_text()

        self.assertIn('host = sys.env("ALLOY_HOST_LABEL")', config)
        self.assertNotIn('host = "deathstar"', config)
        self.assertNotIn('source = "docker"', config)
        self.assertNotIn('source = "nginx"', config)


if __name__ == "__main__":
    unittest.main()
