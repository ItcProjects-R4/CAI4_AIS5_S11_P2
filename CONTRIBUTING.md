# Contributing to Customer Data ETL

The full contribution guide lives in [wiki/Contributing.md](wiki/Contributing.md). This file stays short on purpose so the root of the repo has one simple entry point for contributors.

## Quick Rules
1. Always work on a branch.
2. Keep pull requests focused on one change.
3. Link every PR to an issue.
4. Test before you push.
5. Get review before merging.

## Where Things Go
- ADF pipeline JSON: `adf/pipelines/`
- ADF dataset JSON: `adf/datasets/`
- ADF linked service JSON: `adf/linked_services/`
- SQL scripts: `sql/scripts/`
- Raw source files: `data/raw/`
- Project docs: `docs/`
- Wiki pages: `wiki/`

Do not commit files from `data/clean/`, credentials, or temporary files.
