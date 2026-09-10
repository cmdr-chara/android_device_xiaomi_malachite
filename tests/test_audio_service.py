"""Init service wiring regressions; hardware audio behavior needs device tests."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def audio_services():
    services = []
    for directory in (ROOT / "init", ROOT / "audio"):
        for path in sorted(directory.glob("*.rc")):
            current = None
            for line in path.read_text().splitlines():
                words = line.split("#", 1)[0].split()
                if not words:
                    continue
                if not line[0].isspace():
                    current = None
                    if words[:2] == ["service", "vendor.audio-hal"]:
                        current = {"path": path, "executable": words[2], "options": []}
                        services.append(current)
                elif current is not None:
                    current["options"].append(words)
    return services


class AudioServiceTests(unittest.TestCase):
    def test_audio_hal_has_one_definition_using_the_packaged_executable(self):
        services = audio_services()
        self.assertEqual(len(services), 1, services)
        self.assertEqual(services[0]["executable"],
                         "/vendor/bin/hw/android.hardware.audio.service.malachite")

    def test_replacement_retains_the_mediatek_audio_socket(self):
        replacement = [service for service in audio_services()
                       if service["executable"].endswith(".malachite")]
        self.assertEqual(len(replacement), 1)
        self.assertIn(["socket", "audio_hw_socket", "seqpacket", "0666", "system", "system"],
                      replacement[0]["options"])


if __name__ == "__main__":
    unittest.main()
