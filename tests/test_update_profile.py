import datetime as dt
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import update_profile

class ProfileUpdaterTests(unittest.TestCase):
    def test_activity_discards_repository_names(self):
        days=[{"date":dt.date(2026,7,13),"level":1,"count":2},{"date":dt.date(2026,7,14),"level":1,"count":1}]
        events=[{"type":"PushEvent","created_at":"2026-07-14T12:00:00Z","repo":{"name":"owner/private-name"},"payload":{}},{"type":"CreateEvent","created_at":"2026-07-13T12:00:00Z","repo":{"name":"owner/another-name"},"payload":{"ref_type":"repository"}}]
        rendered=update_profile.render_activity(days,events,dt.date(2026,7,14))
        self.assertIn("3 contributions",rendered);self.assertIn("1 push across 1 public repository",rendered);self.assertIn("Created 1 public repository",rendered)
        self.assertNotIn("private-name",rendered);self.assertNotIn("another-name",rendered);self.assertNotIn("owner/",rendered)
    def test_generated_regions_must_be_unique(self):
        with self.assertRaises(ValueError):update_profile.replace("no markers","START","END","data")
    def test_invalid_calendar_is_rejected(self):
        with self.assertRaises(ValueError):update_profile.validate(1,[{"date":dt.date(2026,7,14),"level":1,"count":1}])
if __name__=="__main__":unittest.main()
