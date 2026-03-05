import json
import os
import threading
import unittest
from editor_server import EditorHandler, ThreadedTCPServer
import socketserver
from http.client import HTTPConnection
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIER_DICT_PATH = os.path.join(BASE_DIR, "tier_dict.json")

class _ServerFixture(unittest.TestCase):
    """Base class that spins up a live EditorHandler server for integration tests."""
    server: ThreadedTCPServer
    server_thread: threading.Thread
    port: int

    @classmethod
    def setUpClass(cls):
        os.chdir(BASE_DIR)
        socketserver.TCPServer.allow_reuse_address = True
        cls.server = ThreadedTCPServer(("127.0.0.1", 0), EditorHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)

class TestEditorDynamicActions(_ServerFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            self._original_content = f.read()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(f"http://localhost:{self.port}/editor.html")
        self.page.wait_for_selector(".logo-item-wrapper", state="attached")

    def tearDown(self):
        self.page.close()
        self.context.close()
        with open(TIER_DICT_PATH, "w", encoding="utf-8") as f:
            f.write(self._original_content)
        super().tearDown()

    def test_drag_and_drop_different_tier_updates_year(self):
        source = self.page.locator('.logo-item-wrapper[data-name="Birdies Fried Chicken"]')
        target = self.page.locator('.tier-content[data-tier="A"]')
        source.drag_to(target)
        self.page.locator('#save-indicator.saved').wait_for(state="attached", timeout=5000)
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            tier_dict = json.load(f)
        import datetime
        current_year = datetime.datetime.now().year
        self.assertIn("Birdies Fried Chicken", tier_dict["A"])
        self.assertEqual(tier_dict["A"]["Birdies Fried Chicken"]["year"], current_year)

    def test_drag_and_drop_same_tier_keeps_year(self):
        source = self.page.locator('.logo-item-wrapper[data-name="Bubba\'s Crispy Fried Chicken"]')
        target = self.page.locator('.logo-item-wrapper[data-name="Zesty Burgers"]')
        source.drag_to(target)
        self.page.locator('#save-indicator.saved').wait_for(state="attached", timeout=15000)
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            tier_dict = json.load(f)
        self.assertIn("Bubba's Crispy Fried Chicken", tier_dict["S"])
        self.assertEqual(tier_dict["S"]["Bubba's Crispy Fried Chicken"]["year"], 2022)

    def test_double_click_opens_editor_and_saves_changes(self):
        item = self.page.locator('.logo-item-wrapper[data-name="Zesty Burgers"]')
        item.dblclick()
        self.page.locator('#edit-modal.active').wait_for(state="attached", timeout=5000)
        self.page.select_option('#edit-price', '4')
        self.page.fill('#edit-description', 'A custom test description')
        self.page.click('#btn-save')
        self.page.locator('#save-indicator.saved').wait_for(state="attached", timeout=5000)
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            tier_dict = json.load(f)
        self.assertEqual(tier_dict["S"]["Zesty Burgers"]["price"], 4)
        self.assertEqual(tier_dict["S"]["Zesty Burgers"]["description"], 'A custom test description')

    def test_unassigned_restaurant_dropdown_creates_new(self):
        # Create a temporary logo to ensure the test always has something to pick
        wait_timeout = 15000
        temp_filename = "_temp_Test_Logo.jpg"
        temp_logo_path = os.path.join(BASE_DIR, "logos", temp_filename)
        os.makedirs(os.path.dirname(temp_logo_path), exist_ok=True)
        with open(temp_logo_path, "wb") as f:
            f.write(b"\xff\xd8\xff") 
        
        import time
        time.sleep(1.0)

        try:
            self.page.reload()
            self.page.wait_for_selector(".logo-item-wrapper", state="visible", timeout=wait_timeout)

            self.page.click('#unassigned-btn')
            self.page.wait_for_selector('.dropdown-menu.show', state="visible", timeout=wait_timeout)
            
            display_name = temp_filename.replace(".jpg", "")
            unassigned_item = self.page.locator('.dropdown-item', has_text=display_name)
            unassigned_item.wait_for(state="visible", timeout=wait_timeout)
            unassigned_item.click()

            # Wait for modal to be fully visible and ready
            self.page.wait_for_selector('#edit-modal.active', state="visible", timeout=wait_timeout)
            
            # Fill REQUIRED fields: Tier, Address, Description
            # Note: edit-name, edit-year, edit-year-first are pre-filled in openCreateModal
            self.page.select_option('#edit-tier', 'B')
            self.page.fill('#edit-address', '123 Fake Street')
            self.page.fill('#edit-description', 'New assigned from unassigned')

            # Click save and wait for success toast
            # Playwright will automatically wait for the button to be enabled/actionable
            save_btn = self.page.locator('#btn-save')
            save_btn.click()
            
            # Wait for "Saved!" toast indicator
            self.page.wait_for_selector('#save-indicator.saved', state="visible", timeout=15000)

            with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
                tier_dict = json.load(f)

            self.assertIn(display_name, tier_dict["B"])
            self.assertEqual(tier_dict["B"][display_name]["address"], '123 Fake Street')
            self.assertEqual(tier_dict["B"][display_name]["description"], 'New assigned from unassigned')
        except Exception:
            # self.page.screenshot(path="test_failure.png")
            raise
        finally:
            if os.path.exists(temp_logo_path):
                os.remove(temp_logo_path)

    def test_zoom_controls_update_zoom_value(self):
        initial_zoom = self.page.locator('#zoom-value').inner_text()
        self.page.click('#zoom-in')
        self.page.wait_for_function(f'document.getElementById("zoom-value").innerText !== "{initial_zoom}"')
        zoomed_in = self.page.locator('#zoom-value').inner_text()
        self.assertNotEqual(initial_zoom, zoomed_in)
        self.page.click('#zoom-out')
        self.page.click('#zoom-out')
        self.page.wait_for_function(f'document.getElementById("zoom-value").innerText !== "{zoomed_in}"')
        zoomed_out = self.page.locator('#zoom-value').inner_text()
        self.assertNotEqual(zoomed_in, zoomed_out)

    def test_year_toggles_show_tags(self):
        self.page.click('#toggle-year-first')
        tags = self.page.locator('.year-tag')
        tags.first.wait_for(state="attached")
        count_tags = tags.count()
        self.assertGreater(count_tags, 0)
        self.page.click('#toggle-year-rerank')
        self.page.wait_for_timeout(500)
        tags2 = self.page.locator('.year-tag')
        self.assertGreater(tags2.count(), 0)

    def test_hover_tooltip_displays_content(self):
        item = self.page.locator('.logo-item-wrapper[data-name="Soy Boys"]')
        item.hover()
        tooltip = self.page.locator('#tooltip')
        tooltip.wait_for(state="visible", timeout=2000)
        self.assertEqual(tooltip.inner_text(), "Soy Boys")

if __name__ == "__main__":
    unittest.main()
