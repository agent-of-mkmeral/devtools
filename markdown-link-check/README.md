# Markdown Link Check

Reusable workflow for weekly markdown link checking across Strands Agents repositories.

## Usage

Add this to your repository at `.github/workflows/check-markdown-links.yml`:

```yaml
name: Check Markdown Links

on:
  schedule:
    - cron: '0 9 * * 1' # Every Monday at 9am UTC
  workflow_dispatch:

jobs:
  check-links:
    uses: strands-agents/devtools/.github/workflows/check-markdown-links.yml@main
```

## Configuration

The workflow uses a default config from this directory. To customize per-repo, add a `.markdown-link-check.json` file to your repository root:

```json
{
  "retryOn429": true,
  "retryCount": 3,
  "fallbackRetryDelay": "30s",
  "aliveStatusCodes": [200, 206]
}
```

If no repo-level config is found, the [default config](./default-config.json) is used automatically.

## How It Works

1. Runs weekly (Monday 9am UTC) or on manual dispatch
2. Scans all markdown files for broken links
3. If broken links are found, creates a GitHub issue with the `broken-links` label
4. Skips issue creation if one already exists (avoids duplicates)
