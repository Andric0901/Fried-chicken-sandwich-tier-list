"""
editor_tests.py

Thorough test suite for the editor component of the tier list application.

Covers:
  - editor_server.py API endpoints (GET /api/data, GET /api/logos,
    POST /api/update, POST /api/rename_logo, POST /api/run_tierlist)
  - evaluate_num_logos_per_row and get_num_rows_per_tier server-side utilities
  - Static file serving (editor.html, editor.css, editor.js)
  - editor.html structural integrity (required IDs / elements present)
  - editor.css required rules present
  - editor.js required function/variable names present
  - tier_dict.json data integrity as seen through the API
  - Security: path traversal protection on rename_logo

Run with:
    python editor_tests.py
  or:
    pytest editor_tests.py
"""

import http.server
import json
import os
import re
import shutil
import socketserver
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from http.client import HTTPConnection

# ---------------------------------------------------------------------------
# Import server-side helpers directly for unit tests (no network needed)
# ---------------------------------------------------------------------------
from editor_server import (
    EditorHandler,
    evaluate_num_logos_per_row,
    get_num_rows_per_tier,
    ThreadedTCPServer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TIER_DICT_PATH = os.path.join(BASE_DIR, "tier_dict.json")
EDITOR_HTML_PATH = os.path.join(BASE_DIR, "editor.html")
EDITOR_CSS_PATH = os.path.join(BASE_DIR, "editor.css")
EDITOR_JS_PATH = os.path.join(BASE_DIR, "editor.js")
LOGOS_DIR = os.path.join(BASE_DIR, "logos")


def _load_tier_dict():
    with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Integration-test fixture: start the server in a background thread
# ---------------------------------------------------------------------------

class _ServerFixture(unittest.TestCase):
    """Base class that spins up a live EditorHandler server for integration tests."""

    server: ThreadedTCPServer
    server_thread: threading.Thread
    port: int

    @classmethod
    def setUpClass(cls):
        # Change cwd so the server can find tier_dict.json and logos/
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

    # ---- convenience helpers ----

    def _get(self, path):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp, body

    def _post(self, path, payload: dict | None = None, raw: bytes | None = None,
              content_type: str = "application/json"):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        if raw is None:
            raw = json.dumps(payload).encode("utf-8") if payload else b""
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(raw)),
        }
        conn.request("POST", path, body=raw, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp, body

    def _json(self, body: bytes) -> dict:
        return json.loads(body.decode("utf-8"))


# ===========================================================================
# 1. Pure unit tests for server utilities (no network)
# ===========================================================================

class TestGetNumRowsPerTier(unittest.TestCase):
    """Unit tests for get_num_rows_per_tier."""

    def _make_dict(self, sizes: dict) -> dict:
        """Build a fake tier_dict with tiers having given entry counts."""
        return {tier: {f"r{i}": {} for i in range(n)} for tier, n in sizes.items()}

    def test_exact_division(self):
        d = self._make_dict({"S": 17, "A": 34})
        result = get_num_rows_per_tier(17, d)
        self.assertEqual(result["S"], 1)
        self.assertEqual(result["A"], 2)

    def test_with_remainder(self):
        d = self._make_dict({"S": 18, "A": 35})
        result = get_num_rows_per_tier(17, d)
        self.assertEqual(result["S"], 2)   # ceil(18/17) = 2
        self.assertEqual(result["A"], 3)   # ceil(35/17) = 3

    def test_empty_tier(self):
        d = self._make_dict({"S": 0, "A": 5})
        result = get_num_rows_per_tier(17, d)
        self.assertEqual(result["S"], 0)

    def test_all_tiers(self):
        sizes = {t: i * 5 for i, t in enumerate("SABCDEF", 1)}
        d = self._make_dict(sizes)
        result = get_num_rows_per_tier(17, d)
        for tier, size in sizes.items():
            expected = size // 17 + (1 if size % 17 != 0 else 0)
            self.assertEqual(result[tier], expected, f"Mismatch for tier {tier}")


class TestEvaluateNumLogosPerRow(unittest.TestCase):
    """Unit tests for evaluate_num_logos_per_row."""

    def _make_dict(self, sizes: dict) -> dict:
        return {tier: {f"r{i}": {} for i in range(n)} for tier, n in sizes.items()}

    def test_returns_integer_in_valid_range(self):
        d = self._make_dict({t: 30 for t in "SABCDEF"})
        result = evaluate_num_logos_per_row(d)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 17)
        self.assertLessEqual(result, 26)  # default threshold = 17+10-1

    def test_deterministic(self):
        d = self._make_dict({t: 30 for t in "SABCDEF"})
        r1 = evaluate_num_logos_per_row(d)
        r2 = evaluate_num_logos_per_row(d)
        self.assertEqual(r1, r2)

    def test_custom_min_val(self):
        d = self._make_dict({t: 20 for t in "SABCDEF"})
        result = evaluate_num_logos_per_row(d, min_val=20, threshold=5)
        self.assertGreaterEqual(result, 20)
        self.assertLessEqual(result, 24)

    def test_single_tier(self):
        d = self._make_dict({"S": 50})
        result = evaluate_num_logos_per_row(d)
        self.assertIsInstance(result, int)

    def test_golden_ratio_direction(self):
        """The chosen value should produce a width/height ratio closer to 1.618
        than the neighbours."""
        from editor_server import DEFAULT_WIDTH, DEFAULT_GAP, GAPS_BETWEEN_RESTAURANTS
        d = self._make_dict({t: 30 for t in "SABCDEF"})
        chosen = evaluate_num_logos_per_row(d)

        def ratio_diff(n):
            rows = get_num_rows_per_tier(n, d)
            w = DEFAULT_WIDTH * (n + 1) + GAPS_BETWEEN_RESTAURANTS * (n - 1) + DEFAULT_GAP * 3
            h = sum(rows[t] * DEFAULT_WIDTH + GAPS_BETWEEN_RESTAURANTS * (rows[t] - 1) for t in rows) \
                + DEFAULT_GAP * (len(rows) + 1)
            return abs(w / h - 1.618)

        diff_chosen = ratio_diff(chosen)
        # Check chosen is no worse than immediate neighbours
        if chosen > 17:
            self.assertLessEqual(diff_chosen, ratio_diff(chosen - 1) + 1e-9)
        if chosen < 26:
            self.assertLessEqual(diff_chosen, ratio_diff(chosen + 1) + 1e-9)


# ===========================================================================
# 2. API: GET /api/data
# ===========================================================================

class TestApiData(_ServerFixture):

    def test_returns_200(self):
        resp, _ = self._get("/api/data")
        self.assertEqual(resp.status, 200)

    def test_content_type_json(self):
        resp, _ = self._get("/api/data")
        self.assertIn("application/json", resp.getheader("Content-Type", ""))

    def test_body_has_tier_dict_key(self):
        _, body = self._get("/api/data")
        data = self._json(body)
        self.assertIn("tier_dict", data)

    def test_body_has_num_logos_per_row(self):
        _, body = self._get("/api/data")
        data = self._json(body)
        self.assertIn("num_logos_per_row", data)
        self.assertIsInstance(data["num_logos_per_row"], int)
        self.assertGreater(data["num_logos_per_row"], 0)

    def test_tier_dict_has_all_tiers(self):
        _, body = self._get("/api/data")
        tier_dict = self._json(body)["tier_dict"]
        for tier in ["S", "A", "B", "C", "D", "E", "F"]:
            self.assertIn(tier, tier_dict,
                          f"tier_dict missing tier '{tier}'")

    def test_tier_dict_restaurants_have_required_fields(self):
        _, body = self._get("/api/data")
        tier_dict = self._json(body)["tier_dict"]
        for tier, restaurants in tier_dict.items():
            for name, info in restaurants.items():
                self.assertIn("path_to_logo_image", info,
                              f"{name} ({tier}) missing path_to_logo_image")
                self.assertIn("year", info,
                              f"{name} ({tier}) missing year")
                self.assertIn("year_first_visited", info,
                              f"{name} ({tier}) missing year_first_visited")

    def test_year_first_visited_not_after_year(self):
        _, body = self._get("/api/data")
        tier_dict = self._json(body)["tier_dict"]
        for tier, restaurants in tier_dict.items():
            for name, info in restaurants.items():
                self.assertLessEqual(
                    info["year_first_visited"], info["year"],
                    f"{name}: year_first_visited ({info['year_first_visited']}) "
                    f"> year ({info['year']})"
                )

    def test_no_cache_header_present(self):
        resp, _ = self._get("/api/data")
        cc = resp.getheader("Cache-Control", "")
        self.assertIn("no-cache", cc)

    def test_cors_header_present(self):
        resp, _ = self._get("/api/data")
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")

    def test_logo_paths_use_logos_prefix(self):
        _, body = self._get("/api/data")
        tier_dict = self._json(body)["tier_dict"]
        for tier, restaurants in tier_dict.items():
            for name, info in restaurants.items():
                self.assertTrue(
                    info["path_to_logo_image"].startswith("logos/"),
                    f"{name}: unexpected logo path '{info['path_to_logo_image']}'"
                )

    def test_restaurant_names_globally_unique(self):
        _, body = self._get("/api/data")
        tier_dict = self._json(body)["tier_dict"]
        all_names = []
        for restaurants in tier_dict.values():
            all_names.extend(restaurants.keys())
        self.assertEqual(len(all_names), len(set(all_names)),
                         "Duplicate restaurant names found across tiers")


# ===========================================================================
# 3. API: GET /api/logos
# ===========================================================================

class TestApiLogos(_ServerFixture):

    def test_returns_200(self):
        resp, _ = self._get("/api/logos")
        self.assertEqual(resp.status, 200)

    def test_content_type_json(self):
        resp, _ = self._get("/api/logos")
        self.assertIn("application/json", resp.getheader("Content-Type", ""))

    def test_body_has_logos_key(self):
        _, body = self._get("/api/logos")
        data = self._json(body)
        self.assertIn("logos", data)

    def test_logos_is_list(self):
        _, body = self._get("/api/logos")
        data = self._json(body)
        self.assertIsInstance(data["logos"], list)

    def test_logos_only_contain_image_files(self):
        _, body = self._get("/api/logos")
        logos = self._json(body)["logos"]
        for logo in logos:
            self.assertTrue(
                logo.lower().endswith((".png", ".jpg", ".jpeg")),
                f"Expected image extension, got: {logo}"
            )

    def test_logos_are_strings(self):
        _, body = self._get("/api/logos")
        logos = self._json(body)["logos"]
        for logo in logos:
            self.assertIsInstance(logo, str)
            self.assertGreater(len(logo), 0)

    def test_cors_header(self):
        resp, _ = self._get("/api/logos")
        self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), "*")


# ===========================================================================
# 4. API: POST /api/update
# ===========================================================================

class TestApiUpdate(_ServerFixture):

    def setUp(self):
        # Read the real tier_dict so we can restore it after each test
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            self._original_content = f.read()

    def tearDown(self):
        with open(TIER_DICT_PATH, "w", encoding="utf-8") as f:
            f.write(self._original_content)

    def test_update_returns_200(self):
        original = _load_tier_dict()
        resp, _ = self._post("/api/update", payload=original)
        self.assertEqual(resp.status, 200)

    def test_update_response_has_success_status(self):
        original = _load_tier_dict()
        _, body = self._post("/api/update", payload=original)
        data = self._json(body)
        self.assertEqual(data.get("status"), "success")

    def test_update_persists_to_disk(self):
        original = _load_tier_dict()
        # Add a sentinel key to one restaurant and post it
        first_tier = next(iter(original))
        first_name = next(iter(original[first_tier]))
        original[first_tier][first_name]["_test_sentinel"] = 42

        resp, _ = self._post("/api/update", payload=original)
        self.assertEqual(resp.status, 200)

        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved[first_tier][first_name].get("_test_sentinel"), 42)

    def test_update_written_as_valid_json(self):
        original = _load_tier_dict()
        self._post("/api/update", payload=original)
        # Should not raise
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            json.load(f)

    def test_update_with_empty_tier_is_accepted(self):
        payload = {t: {} for t in "SABCDEF"}
        resp, body = self._post("/api/update", payload=payload)
        self.assertEqual(resp.status, 200)
        self.assertEqual(self._json(body).get("status"), "success")

    def test_update_preserves_all_tiers_structure(self):
        original = _load_tier_dict()
        self._post("/api/update", payload=original)
        _, body = self._get("/api/data")
        saved_tiers = self._json(body)["tier_dict"]
        self.assertEqual(set(saved_tiers.keys()), set(original.keys()))

    def test_update_with_invalid_json_returns_500(self):
        resp, _ = self._post("/api/update", raw=b"not-valid-json")
        self.assertEqual(resp.status, 500)

    def test_update_content_type_returned_is_json(self):
        original = _load_tier_dict()
        resp, _ = self._post("/api/update", payload=original)
        self.assertIn("application/json", resp.getheader("Content-Type", ""))


# ===========================================================================
# 5. API: POST /api/rename_logo
# ===========================================================================

class TestApiRenameLogo(_ServerFixture):

    def setUp(self):
        # Create a temp logo file inside the logos/ directory for testing
        os.makedirs(LOGOS_DIR, exist_ok=True)
        self._tmp_logo = os.path.join(LOGOS_DIR, "_test_logo_original.jpg")
        self._tmp_logo_new = os.path.join(LOGOS_DIR, "_test_logo_renamed.jpg")
        # Write a tiny placeholder file
        with open(self._tmp_logo, "wb") as f:
            f.write(b"\xff\xd8\xff")  # minimal JPEG header

    def tearDown(self):
        for p in [self._tmp_logo, self._tmp_logo_new]:
            if os.path.exists(p):
                os.remove(p)

    def test_rename_success_returns_200(self):
        resp, body = self._post("/api/rename_logo", payload={
            "old_path": "logos/_test_logo_original.jpg",
            "new_path": "logos/_test_logo_renamed.jpg",
        })
        self.assertEqual(resp.status, 200)
        self.assertEqual(self._json(body).get("status"), "success")

    def test_rename_actually_moves_file(self):
        self._post("/api/rename_logo", payload={
            "old_path": "logos/_test_logo_original.jpg",
            "new_path": "logos/_test_logo_renamed.jpg",
        })
        self.assertFalse(os.path.exists(self._tmp_logo))
        self.assertTrue(os.path.exists(self._tmp_logo_new))

    def test_rename_nonexistent_file_returns_400(self):
        resp, _ = self._post("/api/rename_logo", payload={
            "old_path": "logos/_does_not_exist.jpg",
            "new_path": "logos/_whatever.jpg",
        })
        self.assertEqual(resp.status, 400)

    def test_rename_missing_paths_returns_error(self):
        """Server returns 400 (missing-paths branch) or 500 (exception) for empty payload."""
        resp, _ = self._post("/api/rename_logo", payload={})
        self.assertIn(resp.status, [400, 500],
                      "Expected 400 or 500 for missing old_path/new_path")

    def test_rename_path_traversal_blocked(self):
        """Attempting to escape the logos/ directory should be rejected."""
        resp, _ = self._post("/api/rename_logo", payload={
            "old_path": "logos/../tier_dict.json",
            "new_path": "logos/../tier_dict_hacked.json",
        })
        self.assertEqual(resp.status, 400)

    def test_rename_path_traversal_absolute_blocked(self):
        """Absolute path outside logos/ must be rejected."""
        resp, _ = self._post("/api/rename_logo", payload={
            "old_path": "/etc/passwd",
            "new_path": "logos/passwd.jpg",
        })
        self.assertEqual(resp.status, 400)

    def test_rename_target_outside_logos_blocked(self):
        """Target path outside logos/ must be rejected."""
        resp, _ = self._post("/api/rename_logo", payload={
            "old_path": "logos/_test_logo_original.jpg",
            "new_path": "../evil.jpg",
        })
        self.assertEqual(resp.status, 400)
        # Original file must still exist
        self.assertTrue(os.path.exists(self._tmp_logo))

    def test_rename_response_is_json(self):
        resp, _ = self._post("/api/rename_logo", payload={
            "old_path": "logos/_test_logo_original.jpg",
            "new_path": "logos/_test_logo_renamed.jpg",
        })
        self.assertIn("application/json", resp.getheader("Content-Type", ""))


# ===========================================================================
# 6. Static file serving
# ===========================================================================

class TestStaticFileServing(_ServerFixture):

    def test_editor_html_served(self):
        resp, body = self._get("/editor.html")
        self.assertEqual(resp.status, 200)
        self.assertIn(b"<!DOCTYPE html>", body[:200])

    def test_editor_html_content_type(self):
        resp, _ = self._get("/editor.html")
        ct = resp.getheader("Content-Type", "")
        self.assertIn("html", ct)

    def test_editor_css_served(self):
        resp, body = self._get("/editor.css")
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(body), 0)

    def test_editor_css_content_type(self):
        resp, _ = self._get("/editor.css")
        ct = resp.getheader("Content-Type", "")
        self.assertIn("css", ct.lower())

    def test_editor_js_served(self):
        resp, body = self._get("/editor.js")
        self.assertEqual(resp.status, 200)
        self.assertGreater(len(body), 0)

    def test_editor_js_content_type(self):
        resp, _ = self._get("/editor.js")
        ct = resp.getheader("Content-Type", "")
        self.assertTrue(
            "javascript" in ct.lower() or "text/plain" in ct.lower(),
            f"Unexpected Content-Type for JS: {ct}"
        )

    def test_nonexistent_file_returns_404(self):
        resp, _ = self._get("/does_not_exist_xyz.html")
        self.assertEqual(resp.status, 404)

    def test_html_has_no_cache_header(self):
        resp, _ = self._get("/editor.html")
        cc = resp.getheader("Cache-Control", "")
        self.assertIn("no-cache", cc)

    def test_css_has_cache_header(self):
        resp, _ = self._get("/editor.css")
        cc = resp.getheader("Cache-Control", "")
        self.assertIn("public", cc)

    def test_js_has_cache_header(self):
        resp, _ = self._get("/editor.js")
        cc = resp.getheader("Cache-Control", "")
        self.assertIn("public", cc)


# ===========================================================================
# 7. editor.html structural integrity
# ===========================================================================

class TestEditorHtmlStructure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(EDITOR_HTML_PATH, "r", encoding="utf-8") as f:
            cls.html = f.read()

    def _has_id(self, id_: str):
        return f'id="{id_}"' in self.html

    # ---- required IDs ----
    def test_has_loading_overlay(self):
        self.assertTrue(self._has_id("loading-overlay"))

    def test_has_progress_fill(self):
        self.assertTrue(self._has_id("progress-fill"))

    def test_has_progress_text(self):
        self.assertTrue(self._has_id("progress-text"))

    def test_has_tierlist_container(self):
        self.assertTrue(self._has_id("tierlist-container"))

    def test_has_unassigned_btn(self):
        self.assertTrue(self._has_id("unassigned-btn"))

    def test_has_unassigned_badge(self):
        self.assertTrue(self._has_id("unassigned-badge"))

    def test_has_unassigned_dropdown(self):
        self.assertTrue(self._has_id("unassigned-dropdown"))

    def test_has_toggle_year_first(self):
        self.assertTrue(self._has_id("toggle-year-first"))

    def test_has_toggle_year_rerank(self):
        self.assertTrue(self._has_id("toggle-year-rerank"))

    def test_has_zoom_default(self):
        self.assertTrue(self._has_id("zoom-default"))

    def test_has_zoom_out(self):
        self.assertTrue(self._has_id("zoom-out"))

    def test_has_zoom_value(self):
        self.assertTrue(self._has_id("zoom-value"))

    def test_has_zoom_in(self):
        self.assertTrue(self._has_id("zoom-in"))

    def test_has_run_tierlist_btn(self):
        self.assertTrue(self._has_id("run-tierlist-btn"))

    def test_has_save_indicator(self):
        self.assertTrue(self._has_id("save-indicator"))

    def test_has_tooltip(self):
        self.assertTrue(self._has_id("tooltip"))

    def test_has_edit_modal(self):
        self.assertTrue(self._has_id("edit-modal"))

    def test_has_nav_prev(self):
        self.assertTrue(self._has_id("nav-prev"))

    def test_has_nav_next(self):
        self.assertTrue(self._has_id("nav-next"))

    def test_has_modal_img(self):
        self.assertTrue(self._has_id("modal-img"))

    def test_has_modal_title(self):
        self.assertTrue(self._has_id("modal-title"))

    def test_has_edit_form(self):
        self.assertTrue(self._has_id("edit-form"))

    def test_has_edit_name(self):
        self.assertTrue(self._has_id("edit-name"))

    def test_has_edit_tier(self):
        self.assertTrue(self._has_id("edit-tier"))

    def test_has_edit_price(self):
        self.assertTrue(self._has_id("edit-price"))

    def test_has_edit_year(self):
        self.assertTrue(self._has_id("edit-year"))

    def test_has_edit_year_first(self):
        self.assertTrue(self._has_id("edit-year-first"))

    def test_has_edit_address(self):
        self.assertTrue(self._has_id("edit-address"))

    def test_has_edit_description(self):
        self.assertTrue(self._has_id("edit-description"))

    def test_has_edit_vegan(self):
        self.assertTrue(self._has_id("edit-vegan"))

    def test_has_edit_highlighted(self):
        self.assertTrue(self._has_id("edit-highlighted"))

    def test_has_btn_cancel(self):
        self.assertTrue(self._has_id("btn-cancel"))

    def test_has_btn_save(self):
        self.assertTrue(self._has_id("btn-save"))

    def test_has_edit_original_name(self):
        self.assertTrue(self._has_id("edit-original-name"))

    def test_has_edit_original_tier(self):
        self.assertTrue(self._has_id("edit-original-tier"))

    def test_has_edit_original_price(self):
        self.assertTrue(self._has_id("edit-original-price"))

    def test_has_edit_mode(self):
        self.assertTrue(self._has_id("edit-mode"))

    def test_has_edit_logo_path(self):
        self.assertTrue(self._has_id("edit-logo-path"))

    # ---- external stylesheet linked (no inline style block) ----
    def test_links_editor_css(self):
        self.assertIn('href="editor.css"', self.html)

    def test_no_inline_style_block(self):
        self.assertNotIn("<style>", self.html.lower())

    # ---- external script linked (no inline script block) ----
    def test_links_editor_js(self):
        self.assertIn('src="editor.js"', self.html)

    def test_no_inline_script_block(self):
        # Should not contain a <script> tag with actual code
        # (a bare <script src=...> tag is fine)
        inline_script = re.search(
            r"<script(?![^>]*\bsrc\b)[^>]*>[^<]+", self.html, flags=re.IGNORECASE
        )
        self.assertIsNone(inline_script, "Found inline <script> block in editor.html")

    # ---- all 7 tier options present in the select ----
    def test_tier_select_has_all_options(self):
        for tier in ["S", "A", "B", "C", "D", "E", "F"]:
            self.assertIn(f'<option value="{tier}">{tier}</option>', self.html)

    # ---- price options ----
    def test_price_select_has_all_options(self):
        for val, label in [("1", "$"), ("2", "$$"), ("3", "$$$"), ("4", "$$$$")]:
            self.assertIn(f'<option value="{val}">{label}</option>', self.html)

    # ---- fonts linked ----
    def test_google_fonts_linked(self):
        self.assertIn("fonts.googleapis.com", self.html)

    # ---- DOCTYPE and lang ----
    def test_has_doctype(self):
        self.assertIn("<!DOCTYPE html>", self.html[:50])

    def test_has_lang_en(self):
        self.assertIn('lang="en"', self.html)


# ===========================================================================
# 8. editor.css integrity
# ===========================================================================

class TestEditorCssIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(EDITOR_CSS_PATH, "r", encoding="utf-8") as f:
            cls.css = f.read()

    # ---- CSS variables ----
    def test_has_bg_color_var(self):
        self.assertIn("--bg-color", self.css)

    def test_has_container_bg_var(self):
        self.assertIn("--container-bg", self.css)

    def test_has_tier_color_vars(self):
        for tier in ["s", "a", "b", "c", "d", "e", "f"]:
            self.assertIn(f"--tier-{tier}", self.css)

    # ---- required selectors / classes ----
    def test_has_body_rule(self):
        self.assertIn("body {", self.css)

    def test_has_tierlist_container(self):
        self.assertIn("#tierlist-container", self.css)

    def test_has_controls(self):
        self.assertIn(".controls", self.css)

    def test_has_zoom_controls(self):
        self.assertIn(".zoom-controls", self.css)

    def test_has_run_tierlist_btn(self):
        self.assertIn(".run-tierlist-btn", self.css)

    def test_has_tier_row(self):
        self.assertIn(".tier-row", self.css)

    def test_has_tier_label(self):
        self.assertIn(".tier-label", self.css)

    def test_has_tier_content(self):
        self.assertIn(".tier-content", self.css)

    def test_has_logo_item_wrapper(self):
        self.assertIn(".logo-item-wrapper", self.css)

    def test_has_logo_item(self):
        self.assertIn(".logo-item", self.css)

    def test_has_price_tag(self):
        self.assertIn(".price-tag", self.css)

    def test_has_vegan_tag(self):
        self.assertIn(".vegan-tag", self.css)

    def test_has_tier_label_data_attrs(self):
        for tier in ["S", "A", "B", "C", "D", "E", "F"]:
            self.assertIn(f'.tier-label[data-tier="{tier}"]', self.css)

    def test_has_save_indicator(self):
        self.assertIn(".save-indicator", self.css)

    def test_has_edit_modal(self):
        self.assertIn("#edit-modal", self.css)

    def test_has_modal_content(self):
        self.assertIn(".modal-content", self.css)

    def test_has_loading_overlay(self):
        self.assertIn("#loading-overlay", self.css)

    def test_has_progress_bar(self):
        self.assertIn(".progress-bar", self.css)

    def test_has_progress_fill(self):
        self.assertIn("#progress-fill", self.css)

    def test_has_tooltip(self):
        self.assertIn(".tooltip", self.css)

    def test_has_unassigned_btn(self):
        self.assertIn(".unassigned-btn", self.css)

    def test_has_year_toggle_btn(self):
        self.assertIn(".year-toggle-btn", self.css)

    def test_has_year_tag(self):
        self.assertIn(".year-tag", self.css)

    def test_has_dropdown_menu(self):
        self.assertIn(".dropdown-menu", self.css)

    def test_has_spin_keyframe(self):
        self.assertIn("@keyframes spin", self.css)

    def test_has_drag_over_style(self):
        self.assertIn(".tier-content.drag-over", self.css)

    def test_has_dragging_style(self):
        self.assertIn(".logo-item-wrapper.dragging", self.css)

    def test_has_invalid_input(self):
        self.assertIn(".invalid-input", self.css)

    def test_has_btn_save(self):
        self.assertIn(".btn-save", self.css)

    def test_has_btn_cancel(self):
        self.assertIn(".btn-cancel", self.css)

    def test_inter_font_referenced(self):
        self.assertIn("Inter", self.css)

    def test_no_inline_html(self):
        self.assertNotIn("<style>", self.css)
        self.assertNotIn("</style>", self.css)


# ===========================================================================
# 9. editor.js integrity
# ===========================================================================

class TestEditorJsIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(EDITOR_JS_PATH, "r", encoding="utf-8") as f:
            cls.js = f.read()

    def _has_function(self, name: str):
        return re.search(rf'\bfunction\s+{re.escape(name)}\s*\(', self.js) is not None

    def _has_const(self, name: str):
        return re.search(rf'\bconst\s+{re.escape(name)}\b', self.js) is not None

    def _has_let(self, name: str):
        return re.search(rf'\blet\s+{re.escape(name)}\b', self.js) is not None

    # ---- global variables ----
    def test_has_current_zoom(self):
        self.assertTrue(self._has_let("currentZoom"))

    def test_has_default_zoom(self):
        self.assertTrue(self._has_let("defaultZoom"))

    def test_has_active_year_mode(self):
        self.assertTrue(self._has_let("activeYearMode"))

    def test_has_current_columns(self):
        self.assertTrue(self._has_let("currentColumns"))

    def test_has_global_tier_dict(self):
        self.assertTrue(self._has_let("globalTierDict"))

    def test_has_unassigned_logos(self):
        self.assertTrue(self._has_let("unassignedLogos"))

    def test_has_image_cache(self):
        self.assertTrue(self._has_const("imageCache"))

    def test_has_dragged_element(self):
        self.assertTrue(self._has_let("draggedElement"))

    # ---- required functions ----
    def test_has_apply_zoom(self):
        self.assertTrue(self._has_function("applyZoom"))

    def test_has_update_tooltip_position(self):
        self.assertTrue(self._has_function("updateTooltipPosition"))

    def test_has_get_ordered_restaurants(self):
        self.assertTrue(self._has_function("getOrderedRestaurants"))

    def test_has_update_nav_buttons(self):
        self.assertTrue(self._has_function("updateNavButtons"))

    def test_has_navigate_modal(self):
        self.assertTrue(self._has_function("navigateModal"))

    def test_has_init(self):
        self.assertTrue(self._has_function("init"))

    def test_has_update_unassigned_dropdown(self):
        self.assertTrue(self._has_function("updateUnassignedDropdown"))

    def test_has_render(self):
        self.assertTrue(self._has_function("render"))

    def test_has_handle_drag_start(self):
        self.assertTrue(self._has_function("handleDragStart"))

    def test_has_handle_drag_end(self):
        self.assertTrue(self._has_function("handleDragEnd"))

    def test_has_handle_drag_over(self):
        self.assertTrue(self._has_function("handleDragOver"))

    def test_has_get_drag_after_element(self):
        self.assertTrue(self._has_function("getDragAfterElement"))

    def test_has_handle_drag_leave(self):
        self.assertTrue(self._has_function("handleDragLeave"))

    def test_has_rebuild_tier_dict(self):
        self.assertTrue(self._has_function("rebuildTierDict"))

    def test_has_handle_drop(self):
        self.assertTrue(self._has_function("handleDrop"))

    def test_has_save_to_server(self):
        self.assertTrue(self._has_function("saveToServer"))

    def test_has_load_images_with_progress(self):
        self.assertTrue(self._has_function("loadImagesWithProgress"))

    def test_has_ensure_image_in_cache(self):
        self.assertTrue(self._has_function("ensureImageInCache"))

    def test_has_check_form_changed(self):
        self.assertTrue(self._has_function("checkFormChanged"))

    def test_has_get_form_state(self):
        self.assertTrue(self._has_function("getFormState"))

    def test_has_open_edit_modal(self):
        self.assertTrue(self._has_function("openEditModal"))

    def test_has_open_create_modal(self):
        self.assertTrue(self._has_function("openCreateModal"))

    def test_has_show_modal(self):
        self.assertTrue(self._has_function("showModal"))

    # ---- API endpoint strings ----
    def test_references_api_data(self):
        self.assertIn("/api/data", self.js)

    def test_references_api_logos(self):
        self.assertIn("/api/logos", self.js)

    def test_references_api_update(self):
        self.assertIn("/api/update", self.js)

    def test_references_api_rename_logo(self):
        self.assertIn("/api/rename_logo", self.js)

    def test_references_api_run_tierlist(self):
        self.assertIn("/api/run_tierlist", self.js)

    # ---- init() is called ----
    def test_init_called_at_end(self):
        # init() should appear as a bare call (not just a definition)
        calls = re.findall(r'\binit\s*\(\s*\)', self.js)
        # At minimum there must be 2 occurrences: definition + call
        self.assertGreaterEqual(len(calls), 2,
                                "init() does not appear to be invoked")

    # ---- no inline HTML ----
    def test_no_script_tags(self):
        self.assertNotIn("<script", self.js.lower())
        self.assertNotIn("</script>", self.js.lower())

    # ---- year highlighted suffix logic present ----
    def test_has_highlighted_suffix_logic(self):
        self.assertIn("_highlighted", self.js)

    # ---- tiers array present ----
    def test_has_all_tiers_array(self):
        self.assertIn("'S', 'A', 'B', 'C', 'D', 'E', 'F'", self.js)

    # ---- Escape key handler ----
    def test_has_escape_key_handler(self):
        self.assertIn("Escape", self.js)

    # ---- Arrow key navigation ----
    def test_has_arrow_key_navigation(self):
        self.assertIn("ArrowLeft", self.js)
        self.assertIn("ArrowRight", self.js)


# ===========================================================================
# 10. Data consistency between tier_dict.json and logos/ directory
# ===========================================================================

class TestDataConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(TIER_DICT_PATH, "r", encoding="utf-8") as f:
            cls.tier_dict = json.load(f)
        cls.logos_on_disk = set(os.listdir(LOGOS_DIR)) if os.path.isdir(LOGOS_DIR) else set()

    def test_name_matches_logo_filename(self):
        """Each restaurant name should match logos/<name>.jpg."""
        for tier, restaurants in self.tier_dict.items():
            for name, info in restaurants.items():
                expected_path = f"logos/{name}.jpg"
                self.assertEqual(
                    info["path_to_logo_image"], expected_path,
                    f"{name} ({tier}): expected path '{expected_path}', "
                    f"got '{info['path_to_logo_image']}'"
                )

    def test_logo_files_exist_on_disk(self):
        for tier, restaurants in self.tier_dict.items():
            for name, info in restaurants.items():
                logo_path = os.path.join(BASE_DIR, info["path_to_logo_image"])
                self.assertTrue(
                    os.path.isfile(logo_path),
                    f"Logo file missing on disk: {info['path_to_logo_image']}"
                )

    def test_no_duplicate_names_across_tiers(self):
        all_names = []
        for restaurants in self.tier_dict.values():
            all_names.extend(restaurants.keys())
        self.assertEqual(len(all_names), len(set(all_names)))

    def test_price_values_in_valid_range(self):
        for tier, restaurants in self.tier_dict.items():
            for name, info in restaurants.items():
                if "price" in info:
                    self.assertIn(
                        int(info["price"]), [1, 2, 3, 4],
                        f"{name}: invalid price value {info['price']}"
                    )

    def test_years_are_integers(self):
        for tier, restaurants in self.tier_dict.items():
            for name, info in restaurants.items():
                self.assertIsInstance(
                    info["year"], int,
                    f"{name}: year is not an int"
                )
                self.assertIsInstance(
                    info["year_first_visited"], int,
                    f"{name}: year_first_visited is not an int"
                )

    def test_years_are_plausible(self):
        for tier, restaurants in self.tier_dict.items():
            for name, info in restaurants.items():
                self.assertGreaterEqual(info["year"], 2000,
                                        f"{name}: year too early")
                self.assertLessEqual(info["year"], 2100,
                                     f"{name}: year implausibly far future")
                self.assertGreaterEqual(info["year_first_visited"], 2000)
                self.assertLessEqual(info["year_first_visited"], 2100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
