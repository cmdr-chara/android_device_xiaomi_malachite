# Proprietary filename coverage

`vendor-inventory.json` is the actual output of the read-only checker against device code `6da4bf9433d00cb2cee7bc54331c237290dad8be` and the vendor Git tree collected at `28a87d5dda2c787dc839e76162ded180d59d5d42`. Input hashes are recorded. The extraction/list files are unchanged from the initial source baseline.

All 1,610 list entries resolve to checked-in vendor destinations; all 59 literal fixup targets also resolve. There are 1,609 distinct destinations: `vendor/etc/MNL_Config.xml` appears identically in the GPS and Radio Configs sections. The audit reports this count without rewriting proprietary inputs or generated build files.

Reproduce with the selected-source collector's vendor tree JSON:

```sh
python3 tools/verify_vendor_inventory.py \
  --device-root "$DEVICE_CHECKOUT" \
  --vendor-tree "$SOURCE_EVIDENCE/proprietary_vendor_xiaomi_malachite/tree.json"
```

The checker parses literal fixup keys without executing extraction code. Six unit tests cover renamed/pinned/module entries, malformed paths, missing destinations, grouped keys and refusal to equate filename coverage with binary validation. Together with the candidate/device tests, the local source suite passes 51 tests.

PASS means name presence only. It does not validate ELF dependencies, binary fixup correctness, signatures, regional firmware compatibility, or camera runtime. Preserve the OS2 camera baseline and the original fixups pending real binary/build/device evidence.
