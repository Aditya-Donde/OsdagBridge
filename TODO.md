# TODO - OSI validation fixes

- [ ] Inspect current OSIValidator logic in `src/osdagbridge/desktop/ui/utils/test_Osi.py` to find why invalid values are treated as valid.
- [ ] Identify the specific bug (likely wrong YAML flattening / key mapping / missing-field vs wrong-value handling).
- [ ] Update ONLY `test_Osi.py` so that range/completeness checks correctly fail on incorrect inputs.
- [ ] Run relevant tests (pytest) to confirm the fix.

