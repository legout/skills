"""Focused contracts for the selectively refreshed draw.io tools (stdlib only)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/visualization/drawio-skill/scripts"


class DrawioCliTests(unittest.TestCase):
    def test_validator_reports_actionable_json_for_dangling_endpoint(self):
        # A source diagram must not be accepted when an edge points nowhere.
        xml = ('<mxfile><diagram name="Page-1"><mxGraphModel><root>'
               '<mxCell id="0"/><mxCell id="1" parent="0"/>'
               '<mxCell id="edge" parent="1" edge="1" target="missing"/>'
               '</root></mxGraphModel></diagram></mxfile>')
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.drawio"
            source.write_text(xml)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate.py"), str(source), "--json"],
                text=True, capture_output=True,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["errors"], 1)
        finding = report["findings"][0]
        self.assertEqual(finding["code"], "E-DANGLING-END")
        self.assertEqual(finding["subject"], "edge")
        self.assertTrue(finding["fix"])


if __name__ == "__main__":
    unittest.main()
