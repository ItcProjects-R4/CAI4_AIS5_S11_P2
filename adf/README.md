# ADF Project Layout

## `adf/source`
Source-controlled JSON artifacts used by Azure Data Factory Git integration:
- `factory`: Factory-level definition and settings
- `linkedService`: Connectivity definitions
- `dataset`: Input/output dataset contracts
- `pipeline`: Orchestration logic
- `dataflow`: Data transformation logic
- `trigger`: Schedules and event triggers
- `integrationRuntime`: Runtime definitions
- `globalParameters`: Shared environment parameters

## `adf/arm_templates`
Published ARM templates and parameter files by environment:
- `dev`
- `test`
- `prod`

Keep template files deterministic and environment values in parameter files.

