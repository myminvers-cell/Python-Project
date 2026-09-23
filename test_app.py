"""
Automated unit & integration tests for UniVault Flask Application.
Tests routing, database queries, search/filters, upvotes, reviews, and uploads.
"""

import unittest
import json
from app import app
import database

class UniVaultTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            database.init_db()

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"UniVault", res.data)
        self.assertIn(b"College Notes & University Exam Material", res.data)

    def test_list_materials(self):
        res = self.client.get("/api/materials")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("materials", data)
        self.assertGreater(data["total"], 0)

    def test_search_materials(self):
        res = self.client.get("/api/materials?search=Operating")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(len(data["materials"]), 0)
        self.assertIn("Operating", data["materials"][0]["title"] + data["materials"][0]["subject_name"])

    def test_filter_by_branch(self):
        res = self.client.get("/api/materials?branch=Computer%20Science%20%26%20Engineering")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        for item in data["materials"]:
            self.assertEqual(item["branch"], "Computer Science & Engineering")

    def test_filter_by_type(self):
        res = self.client.get("/api/materials?material_type=Previous%20Year%20Questions%20(PYQs)")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        for item in data["materials"]:
            self.assertEqual(item["material_type"], "Previous Year Questions (PYQs)")

    def test_get_single_material(self):
        res = self.client.get("/api/materials/1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["id"], 1)
        self.assertIn("reviews", data)

    def test_upvote_material(self):
        res_before = self.client.get("/api/materials/1")
        count_before = res_before.get_json()["upvotes_count"]

        res = self.client.post("/api/materials/1/upvote")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["upvotes_count"], count_before + 1)

    def test_download_tracking(self):
        res = self.client.post("/api/materials/1/download")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["downloads_count"], 0)

    def test_submit_review(self):
        review_payload = {
            "author_name": "Test Student",
            "rating": 5,
            "comment": "Exceptional notes, perfectly organized for quick revision!"
        }
        res = self.client.post(
            "/api/materials/1/reviews",
            data=json.dumps(review_payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])

    def test_upload_material(self):
        new_material = {
            "title": "Quantum Mechanics & Semiconductor Physics",
            "subject_name": "Engineering Physics",
            "subject_code": "PH-101",
            "branch": "Applied Sciences & Mathematics",
            "semester": "Semester 1",
            "university": "MIT",
            "material_type": "Lecture Notes",
            "description": "Schrodinger wave equation, tunneling effect, and energy band diagrams.",
            "uploader_name": "Niels Bohr Jr.",
            "tags": "Physics,Quantum,Semiconductors"
        }
        res = self.client.post(
            "/api/materials",
            data=json.dumps(new_material),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("material_id", data)

    def test_platform_stats(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_materials", data)
        self.assertIn("total_downloads", data)

    def test_leaderboard(self):
        res = self.client.get("/api/leaderboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    unittest.main()
