---
name: azure-update-powerpoint
description: Plan or generate this repository's recurring Azure Update PowerPoint deck. Use when asked for the next Azure update deck, the commands or date range to use, or to create azure_update_*.md and pptx_azure_update_*.pptx files.
---

# Azure Update PowerPoint

Use this skill only for the Azure Update workflow in this repository.

Treat `README.md`, `1_get_azure_update.py`, and
`2_make_jp_update_pptx.py` as the source of truth. Read them before giving
commands or generating files. Do not infer the workflow from filenames alone.

## Separate planning from execution

Determine the user's intent before running anything:

- If the user asks for commands, a plan, a review, or says not to run yet,
  perform read-only inspection and provide the commands. Do not run either
  Python script, authenticate, install packages, or create output files.
- If the user explicitly asks to create or generate the deck, run the workflow
  end to end and validate the result.
- If execution intent is genuinely ambiguous, ask whether they want commands
  only or actual generation.

Never turn a request to "think about" or "tell me the commands" into an
execution request.

## Determine the covered-through date

Do not choose the baseline by creation time alone.

1. Enumerate non-empty PowerPoint files matching:

   ```text
   pptx_azure_update_YYYYMMDD_YYYYMMDD.pptx
   pptx_azure_update_YYYYMMDD_YYYYMMDD_<variant>.pptx
   ```

2. Ignore service-specific files whose range does not immediately follow
   `pptx_azure_update_`, such as `pptx_azure_update_API_Management_*.pptx`.
3. Parse the second date from every matching filename and select the greatest
   date. This is the previous deck's covered-through date.
4. If both standard and variant decks share that date, use the shared date as
   the baseline. Prefer the unsuffixed deck when referring to the standard
   workflow.
5. If no valid deck exists, stop and explain that the baseline cannot be
   determined.

## Apply the repository's date convention

Use the previous deck's covered-through date as the next fetch start date.
Existing sequential decks follow this convention:

```text
..._20260323_20260420.pptx
..._20260420_20260518.pptx
..._20260518_20260622.pptx
```

`1_get_azure_update.py` includes updates whose modified date equals the
specified date. Therefore, the boundary date can overlap. Describe this
accurately; do not silently add one day or claim there is no overlap. Reusing
the boundary date avoids missing updates added later on that date.

Only use the following day when the user explicitly requests strict exclusion
of all updates dated on the previous boundary.

## Distinguish standard and curated decks

The README documents the standard workflow that fetches all matching Azure
updates and generates one slide per Markdown entry.

Files with an additional suffix are curated variants. There is no
documented automated slimming step in this repository. Never claim that the
README workflow reproduces a curated variant.

If the user asks for a deck matching a curated variant, first establish the
selection criteria or request the curated Markdown input. Otherwise, use the
standard full-deck workflow.

## Prepare README-aligned commands

For an existing Windows checkout, use the repository virtual environment
directly:

```powershell
Set-Location '<repository-root>'

$python = '.\venv\Scripts\python.exe'
$from = '<YYYY-MM-DD covered-through date>'
$today = Get-Date -Format 'yyyyMMdd'
$md = "azure_update_$($from.Replace('-', ''))_$today.md"

$env:PYTHONIOENCODING = 'utf-8'

& $python .\1_get_azure_update.py $from
& $python .\2_make_jp_update_pptx.py $md
```

Passing the Markdown filename explicitly is required for reliability.
`2_make_jp_update_pptx.py` otherwise chooses a file by creation time, which can
select a scoped, curated, partial, or otherwise unintended Markdown file.

Using `venv\Scripts\python.exe` is operationally equivalent to activating the
environment as shown in the README. Call it "README-aligned," not "the exact
README commands." If the user asks for the literal setup sequence, show:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
```

Do not reinstall dependencies when the existing environment already imports
the required packages.

## Preflight before execution

When generation is requested:

1. Confirm the virtual-environment Python exists.
2. Confirm `.env` defines `AZURE_OPENAI_ENDPOINT` and
   `MODEL_DEPLOYMENT_NAME`, without displaying their values.
3. Confirm the required Python imports work. Install from
   `requirements.txt` only after a missing-dependency failure.
4. Check `az account show`. Run `az login` only if authentication is missing
   or expired.
5. Check whether the expected Markdown or PowerPoint output already exists.
   Do not overwrite a non-empty artifact without making that clear to the
   user. A zero-byte or demonstrably partial artifact may be replaced during
   an explicitly requested generation.
6. Set `PYTHONIOENCODING=utf-8` on Windows to prevent Japanese console output
   from failing under a legacy encoding.

Never print `.env` contents, tokens, endpoints, tenant identifiers, or account
details.

## Execute and validate

When the user explicitly requests generation:

1. Run `1_get_azure_update.py` with the determined boundary date.
2. Require a successful exit and a non-empty expected Markdown file.
3. Count non-empty sections separated by 50 equals signs and report the entry
   count before invoking Azure OpenAI.
4. Run `2_make_jp_update_pptx.py` with that exact Markdown filename.
5. Require a successful exit and a non-empty expected PowerPoint file.
6. Open the PowerPoint with `python-pptx` and verify that its slide count
   equals the Markdown entry count.
7. Report the exact Markdown and PowerPoint filenames.

If fetching or generation fails, surface the actual error. Do not present a
partial or zero-byte file as a completed artifact.

## Answering alignment questions

When asked whether commands align with the README, compare them explicitly:

- Date argument to `1_get_azure_update.py`: documented.
- Explicit Markdown argument to `2_make_jp_update_pptx.py`: documented.
- Direct virtual-environment interpreter: equivalent to activation, but not
  literally the same command.
- Conditional Azure login: equivalent to the README prerequisite.
- UTF-8 environment setting: an additional Windows reliability measure.
- Curated or slim filtering: not documented.

State "aligned" only after making these distinctions.
