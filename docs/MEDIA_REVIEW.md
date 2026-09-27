# Media review and the canonical media gate

Two related decisions live here:

1. **Which rule decides whether an image ships in the canonical release.**
2. **Who is allowed to assign the moderation scores that rule can require.**

Both are deliberate. Neither is inferred from a username, and no score is ever
invented to make a record pass.

## The problem this solves

The canonical release used to require `authenticity_score >= 0.85` and
`destination_match_score >= 0.85`. The imported database had `NULL` in both
columns, so almost every image was excluded and the published release carried
**723** images while the running site displayed roughly **14,861**.

Meanwhile several import paths were writing *fixed* values (`0.9`, `0.75`,
`1.0`, `0.65`) so records would clear that gate. A gate that invented its own
input is not a gate. Those constants are gone: import and automation paths now
leave the score `NULL` and the image reports as *awaiting media review*.

That leaves a real choice, so the project makes it explicitly.

## Option 1 — match the gate to the application (`approval`)

The website already has a working rule: `verification_status = approved`,
`is_verified = true`, an external URL, and a name-match proving the photo is of
*that* place. The release can adopt exactly that rule and stop demanding scores
nobody legitimately set.

```bash
PUBLIC_SNAPSHOT_MEDIA_GATE=approval python manage.py build_verified_snapshot --as-of ... --force
```

Result: the release matches what the site shows, and nothing is invented.

## Option 2 — keep the scored gate and review properly (`scored`)

The scored gate stays, but the scores must now come from a real, named,
authorised reviewer. Set the gate explicitly:

```bash
PUBLIC_SNAPSHOT_MEDIA_GATE=scored python manage.py build_verified_snapshot --as-of ... --force
```

Images then move through review (below) and enter the release only once both
scores are present, high enough, **and** carry provenance.

### Provenance, and why legacy scores are excluded

A score only counts when a named reviewer stands behind it:

| Column | Meaning |
| --- | --- |
| `authenticity_score` / `_by` / `_at` | value, who assigned it, when |
| `destination_match_score` / `_by` / `_at` | value, who assigned it, when |
| `media_reviewed_by` / `_at` | who last made an approve/reject decision |

Existing scores are **not** backfilled. Rewriting them would be a worse lie
than the gap. So a pre-existing `0.9` written by an import script has no
reviewer, is reported as `authenticity_score_unreviewed`, and stays out of the
scored release until a human reviews it. Set
`PUBLIC_SNAPSHOT_REQUIRE_REVIEW_PROVENANCE=false` only if you deliberately want
unattributed scores to count.

### What ships and what does not

A public release never names the person who reviewed anything — the data policy
already excludes reviewer IDs, and accounts are not in the snapshot, so a user
foreign key would dangle. Therefore:

| | In the live database / admin API | In the public release |
| --- | --- | --- |
| `authenticity_score_by`, `destination_match_score_by`, `media_reviewed_by` | yes — who assigned it | **stripped** |
| `*_at` timestamps | yes | yes |
| `authenticity_score` / `destination_match_score` | yes | yes |

The release therefore proves *that* a review happened (a recorded timestamp)
without publishing *who* did it. The named reviewer is available to operators
through `GET /api/v1/admin/media-review/<image_id>` and the audit log.

## Who may review — permissions, not role names

Four Django permissions on `DestinationImage` (granted, never assumed):

| Permission | Allows |
| --- | --- |
| `tourist.review_destinationimage` | perform a review |
| `tourist.assign_destinationimage_authenticity` | set the authenticity score |
| `tourist.assign_destinationimage_destination_match` | set the destination-match score |
| `tourist.approve_destinationimage_review` | approve or reject the result |

An admin or manager may review directly, and may **delegate** to an eligible
member. The grant records who gave it and when, and is itself audited.

```bash
# Who may I review, and who granted it?
GET /api/v1/admin/media-review/capabilities

# An admin delegates review + authenticity to one member
POST /api/v1/admin/media-review/delegation
{"email": "member@example.com",
 "actions": ["review", "score_authenticity"],
 "grant": "true"}

# A reviewer records real judgements (values are required, never defaulted)
POST /api/v1/admin/media-review/<image_id>/score
{"authenticity_score": 0.94, "destination_match_score": 0.91, "note": "verified on Commons"}

# The reviewer's work queue: images the site shows but the gate holds back
GET /api/v1/admin/media-review/queue?state=eligible_under_application_rule
```

A member with no granted permission gets `403` and no score is written.

## The four states a record can be in

`GET /api/v1/admin/media-review/queue` returns `review_state` per image:

| State | Meaning |
| --- | --- |
| `approved_for_canonical_release` | passes the **active** gate — ship it |
| `reviewed_below_threshold` | a reviewer judged it and it genuinely fell short |
| `eligible_under_application_rule` | the site already displays it, but the active gate holds it back (scored gate with no provenance, missing attribution); a media review is the next action |
| `awaiting_media_review` | the site does not display it either — it needs approval or better media data before a reviewer can score it |

The states are non-overlapping, so a reviewer queue built on them contains only
work that a reviewer can actually perform.

Each row also carries `canonical_exclusion_reason`
(`awaiting_media_review`, `authenticity_score_unreviewed`,
`authenticity_score_below_threshold`, `not_destination_specific`, …) so a UI can
say *why* rather than showing an empty list.

## Which rule is active?

Never guess — ask:

```bash
python manage.py snapshot_media_exclusions
python manage.py snapshot_media_exclusions --json
```

It prints the active gate, the threshold, whether provenance is required, the
state counts, and per-reason exclusion counts with example image ids. The
active rule is also written into every release as
`policy.media_gate` in `verified_tourism_data.json`, so a downloaded artifact
always states which rule produced it.

## Configuration reference

| Setting / env var | Default | Meaning |
| --- | --- | --- |
| `PUBLIC_SNAPSHOT_MEDIA_GATE` | `scored` | `scored` or `approval` |
| `PUBLIC_SNAPSHOT_SCORE_THRESHOLD` | `0.85` | minimum for both scores |
| `PUBLIC_SNAPSHOT_REQUIRE_REVIEW_PROVENANCE` | `true` | ignore scores with no named reviewer |

Defaults preserve today's behaviour. Switching the gate changes the payload
digest, so a rebuild is required — and the release records the change rather
than hiding it.
