---
name: azure-update-powerpoint
description: Plan or generate the next recurring Azure Update PowerPoint deck in this repository. Use for choosing its date range, commands, inputs, or output filenames.
---

# Azure Update PowerPoint

Follow `README.md` for setup and the documented two-script workflow. Apply
only the additional rules below.

## Choose the date range

1. Consider non-empty standard decks named exactly
   `pptx_azure_update_YYYYMMDD_YYYYMMDD.pptx`.
2. Ignore service-specific or suffixed deck filenames.
3. Use the greatest ending date as the next fetch start date.
4. Use the current local date as the output ending date.

The fetch date is inclusive. Reusing the previous ending date may overlap
boundary-day records, but avoids missing records added later on that date.
Advance it by one day only when the user explicitly requests no overlap.

If no standard deck exists for the latest period, stop instead of inferring a
baseline from another kind of artifact.

## Resolve ambiguous statuses

After fetching, search the generated Markdown for `<!-- status-review`.
If none exists, continue to PowerPoint generation.

For each flagged entry:

1. Read its existing reference links first.
2. If necessary, search official Microsoft documentation for explicit
   lifecycle wording.
3. Change `要確認` to one of `一般提供`, `パブリックプレビュー`,
   `プライベートプレビュー`, `開発中`, `リタイアメント`, or
   `その他の更新`.
4. Add the official evidence URL under `参考リンク` if it is not already
   present, then remove the `status-review` comment.

Do not change unflagged categories. If official sources do not resolve the
category, leave the entry flagged rather than guessing.

## Run reliably

- Run the README workflow directly. Add diagnostic commands only after a
  documented command fails.
- On Windows, set `PYTHONIOENCODING=utf-8` before fetching.
- Always pass the exact generated Markdown filename to
  `2_make_jp_update_pptx.py`; do not rely on its creation-time-based automatic
  selection.
- The documented workflow creates the full deck. Do not infer undocumented
  filtering from other local artifacts.
- Do not copy local artifact suffixes into public changes or responses.

## Validate generated artifacts

- Do not overwrite a non-empty expected output without explicit approval.
- Require the generated Markdown and PowerPoint files to be non-empty.
- Verify that the PowerPoint slide count equals the number of non-empty
  Markdown sections separated by 50 equals signs.

## Reference timing

One observed run on 2026-07-21 used `gpt-5.6-sol` for 43 updates,
including 13 status reviews:

| Phase | Time |
|---|---:|
| Fetch | 15.2s |
| Status scan | 11.0s |
| Status research | 105.5s |
| PowerPoint generation | 175.5s |
| Validation | 32.8s |
| Total | 5m 40s |

This is a planning example, not a performance target. Generation time varies
mainly with slide count and model latency; research time varies with the number
and complexity of ambiguous statuses. Replace this example only when it is no
longer representative. Do not accumulate run history here.
