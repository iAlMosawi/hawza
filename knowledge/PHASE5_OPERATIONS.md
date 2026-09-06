# Noor Al-Hawza Phase 5 Operations

## Safety model

The existing `hawza_knowledge.sqlite` remains the only knowledge database.
Schema v2 adds metadata without removing any v1 table or column.  Runtime code
must detect v1 capability and treat released v1 sources as `legacy_trusted`.

New manifest sources are `pending` unless an authorised reviewer explicitly
sets `review_status: approved`.  `official_source`, `is_current`, and `marja`
are null until curated metadata is supplied.  Automation must never assign
those values.

## Staged release

Run these commands from the Hawza repository.  They create a new database and
do not change the active production database:

```bash
python knowledge/build/build_knowledge.py \
  --output /tmp/hawza_knowledge.sqlite \
  --quality-report /tmp/hawza_knowledge.quality.json
python knowledge/build/validate_knowledge.py \
  --db /tmp/hawza_knowledge.sqlite --require-phase5
shasum -a 256 /tmp/hawza_knowledge.sqlite
```

Only after review of the quality report, checksum, integrity check, and API
smoke tests should an operator deploy the staged file.  Keep the current
database and checksum as a rollback copy.  The server update process is:

```bash
# operator runbook: paths must be adjusted for the deployment account
cp /var/lib/noor/hawza_knowledge.sqlite /var/lib/noor/hawza_knowledge.rollback.sqlite
cp /tmp/hawza_knowledge.sqlite /var/lib/noor/hawza_knowledge.next.sqlite
sqlite3 /var/lib/noor/hawza_knowledge.next.sqlite 'PRAGMA integrity_check;'
mv /var/lib/noor/hawza_knowledge.next.sqlite /var/lib/noor/hawza_knowledge.sqlite
sudo systemctl restart gunicorn.service
```

## Rollback

If a smoke test fails, atomically restore the saved known-good database and
restart the service:

```bash
cp /var/lib/noor/hawza_knowledge.rollback.sqlite /var/lib/noor/hawza_knowledge.rollback.next.sqlite
mv /var/lib/noor/hawza_knowledge.rollback.next.sqlite /var/lib/noor/hawza_knowledge.sqlite
sudo systemctl restart gunicorn.service
```

## Human review still required

- Replace or manually repair the text extraction for `diyafa_ramadan.pdf`.
- Classify every legacy source with a controlled category/subcategory.
- Review and explicitly set authority metadata for any marja-specific source.
- Approve new sources before enabling them as production evidence.
