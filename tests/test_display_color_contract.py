"""Guards for the malachite display color pipeline."""

import os
from pathlib import Path
import unittest


ROOT = Path(os.environ.get("MALACHITE_DEVICE_ROOT", Path(__file__).resolve().parents[1]))


class DisplayColorContractTests(unittest.TestCase):
    def test_global_saturation_is_neutral(self):
        properties = dict(
            line.split("=", 1)
            for raw in (ROOT / "vendor.prop").read_text().splitlines()
            if (line := raw.partition("#")[0].strip()) and "=" in line
        )
        # Stock does not set this property, so SurfaceFlinger's 1.0 default applies.
        # A 1.1 override shifts saturated reds toward the reported pink/magenta hue.
        self.assertIn(properties.get("persist.sys.sf.color_saturation", "1.0"), {"1", "1.0"})


if __name__ == "__main__":
    unittest.main()
