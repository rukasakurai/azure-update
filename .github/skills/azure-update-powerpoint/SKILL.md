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

## Run reliably

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
