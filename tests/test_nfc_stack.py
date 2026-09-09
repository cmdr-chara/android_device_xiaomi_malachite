"""Cross-file NFC provider contracts; hardware stability is tested on-device."""
import os
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from test_nfc_initialization import actions


ROOT = Path(os.environ.get("NFC_TEST_DEVICE_ROOT", Path(__file__).resolve().parents[1]))
SKUS = {"hcesim_dsds", "hcesim_ss", "hcesimese_dsds"}
NFC_NAMES = {"android.hardware.nfc", "vendor.tms.tmsnfc", "vendor.tms.tmsnfc_aidl"}


class NfcStackTests(unittest.TestCase):
    def test_each_nfc_sku_has_one_matching_aidl_provider_and_extension(self):
        for manifest in [ROOT / "manifest.xml", *sorted((ROOT / "vintf").glob("*.xml"))]:
            with self.subTest(manifest=manifest.name):
                hals = [hal for hal in ET.parse(manifest).getroot().findall("hal")
                        if hal.findtext("name") in NFC_NAMES]
                sku = manifest.stem.removeprefix("manifest_")
                expected = {"android.hardware.nfc": "INfc/default",
                            "vendor.tms.tmsnfc_aidl": "ITmsNfc/default"} if sku in SKUS else {}
                self.assertEqual(len(hals), len(expected))
                self.assertEqual({hal.findtext("name") for hal in hals}, set(expected))
                for hal in hals:
                    self.assertEqual(hal.get("format"), "aidl")
                    self.assertEqual(hal.findtext("version"), "1")
                    self.assertIsNone(hal.find("transport"))
                    self.assertEqual([item.text for item in hal.findall("fqname")],
                                     [expected[hal.findtext("name")]])
        matrix_hals = [hal for hal in ET.parse(ROOT / "framework_compatibility_matrix.xml")
                       .getroot().findall("hal") if hal.findtext("name") in NFC_NAMES]
        self.assertEqual(len(matrix_hals), 1)
        self.assertEqual(matrix_hals[0].findtext("name"), "vendor.tms.tmsnfc_aidl")
        self.assertEqual(matrix_hals[0].get("format"), "aidl")
        # India has no NFC provider, so the device extension cannot be mandatory.
        self.assertEqual(matrix_hals[0].get("optional"), "true")

    def test_init_enables_only_the_declared_provider_on_nfc_skus(self):
        rc = ROOT / "init/init.nfc.malachite.rc"
        services = re.findall(r"(?m)^service (\S+) (\S*nfc\S*)\s*$", rc.read_text())
        self.assertEqual(len(services), 1)
        service, executable = services[0]
        self.assertEqual(executable, "/vendor/bin/hw/android.hardware.nfc-service-tms")
        service_body = rc.read_text().split("service " + service + " ", 1)[1]
        service_body = re.split(r"\n\S", service_body, maxsplit=1)[0]
        self.assertRegex(service_body, r"(?m)^\s+disabled\s*$")
        by_trigger = actions(rc)
        actual = {trigger for trigger, commands in by_trigger.items()
                  if ["enable", service] in commands}
        self.assertEqual(actual, {
            "early-init && property:ro.boot.hwc=CN",
            "early-init && property:ro.boot.hwc=Global && property:ro.boot.multisim=dsds",
            "early-init && property:ro.boot.hwc=Global && property:ro.boot.multisim=ss",
        })
        self.assertFalse(any(command[0] in {"start", "enable"} and "nfc" in command[1]
                             for trigger, commands in by_trigger.items() if "India" in trigger
                             for command in commands))

    def test_selected_executable_is_extracted_pinned_and_has_its_domain_label(self):
        lines = [line for line in (ROOT / "proprietary-files.txt").read_text().splitlines()
                 if line.startswith("vendor/bin/hw/android.hardware.nfc-service-tms")]
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^vendor/bin/hw/android\.hardware\.nfc-service-tms\|[0-9a-f]{40}$")
        executable = "/" + lines[0].split("|", 1)[0]
        labels = [words[1] for line in (ROOT / "sepolicy/vendor/file_contexts").read_text().splitlines()
                  if len(words := line.split()) == 2 and re.fullmatch(words[0], executable)]
        self.assertEqual(labels, ["u:object_r:hal_nfc_default_exec:s0"])
        entries = (ROOT / "proprietary-files.txt").read_text()
        self.assertNotIn("odm/bin/hw/android.hardware.nfc@1.2-service-tms", entries)
        self.assertNotIn("vendor/lib64/vendor.tms.nfc-V1-ndk.so", entries)
        # Stock COS helpers still consume this interface library.
        self.assertIn("vendor/lib64/vendor.tms.tmsnfc@1.0.so|", entries)


if __name__ == "__main__":
    unittest.main()
