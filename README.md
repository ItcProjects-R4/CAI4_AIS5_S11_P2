# ETL لبيانات العملاء من مصادر متعددة
# Customer Data ETL from Multiple Sources

[العربية](#العربية) | [English](#english)

---

## English

### Overview

**Customer Data ETL** is a production-grade, container-first Python project that integrates customer data from multiple sources (CRM systems and Excel files), cleans and transforms it, and produces a data warehouse-ready dataset for analysis.

**Tech Stack:** Python 3.10+, Docker, docker-compose, pytest, pandas, pyodbc, python-dotenv, openpyxl

**Team Roles:**
- Data Extraction (استخراج البيانات)
- Data Cleaning & Transformation (تنظيف وتحويل البيانات)
- Data Modeling & Warehouse Design (نمذجة البيانات وتصميم المستودع)
- Data Validation & Testing (التحقق من صحة البيانات والاختبار)
- Documentation & Presentation (التوثيق والعرض)

### Quick Start with Docker

All development happens inside Docker. No need to install Python or dependencies on your host machine.

#### Setup

```bash
# 1. Copy the environment template
cp .env.template .env

# 2. Edit .env with your database credentials (if needed for development)
#    For initial testing, defaults will work
nano .env

# 3. Build the Docker image
docker compose build

# 4. Verify your environment inside Docker
docker compose run --rm etl python -m etl_cli check_env

# 5. Generate mock data for testing
docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42
```

#### Run Commands Inside Docker

```bash
# Open an interactive shell inside the container
docker compose run --rm etl bash

# Run all tests
docker compose run --rm etl pytest

# Run linting
docker compose run --rm etl flake8 src tests

# Run formatting check
docker compose run --rm etl black --check src tests

# Run the ETL pipeline (placeholder)
docker compose run --rm etl python -m etl_cli run_pipeline

# Clean up generated data
docker compose run --rm etl python -m etl_cli clean
```

#### Or Use Make Targets

```bash
make build          # Build Docker image
make up             # Start container in the background
make shell          # Open interactive shell in container
make test           # Run pytest
make lint           # Run flake8
make fmt            # Format code with black
make clean          # Remove generated artifacts
make clean-docker   # Stop and remove containers
```

### Project Phases

The project is organized in phases to help structure development:

- **Phase 1:** Project scaffolding and Docker environment setup ✓
- **Phase 2:** Generate mock data and verify environment (run `make shell` then `python -m etl_cli generate_mock_data --seed 42 --rows 50`)
- **Phase 3:** Environment checks and diagnostic tools (run `python -m etl_cli check_env`)
- **Phase 4:** Implement ETL pipeline and business logic

### File Structure

```
.
├── src/
│   ├── __init__.py
│   └── etl_cli/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── check_env.py        # Environment diagnostics
│       ├── generate_mock_data.py # Mock data generator
│       ├── setup.py            # Setup utilities
│       └── pipeline.py         # Pipeline skeleton
├── tests/
│   ├── __init__.py
│   ├── test_check_env.py
│   └── test_generate_mock_data.py
├── data/
│   ├── raw/                    # Generated mock data here
│   └── clean/                  # Cleaned data output
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
├── sql/                        # SQL artifacts (future)
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env.template
├── .gitignore
├── .pre-commit-config.yaml
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md (this file)
```

### Development Workflow

1. **Never edit code directly on your host.** Edit in your editor, but execute inside Docker.
2. **Environment secrets:** Create `.env` from `.env.template`. Always add `.env` to `.gitignore` (already done).
3. **Git:** Use feature branches. Every PR must pass linting and tests.
4. **Pre-commit hooks:** Install locally with `pre-commit install` to catch issues before commit.
5. **Tests:** Write tests for all new modules. Run `make test` before pushing.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'pyodbc'` | This is expected if ODBC drivers aren't installed. Run `docker compose run --rm etl python -m etl_cli check_env` to see what's missing. |
| `PermissionError: Cannot write to data/` | Ensure you're running inside the Docker container, not on the host. |
| `docker: command not found` | Install Docker from https://docs.docker.com/get-docker/ |
| `Port 5432 already in use` | Change `docker-compose.yml` if you added a DB service. For now, no ports are exposed. |
| Tests pass locally but fail in CI | CI runs in a fresh Docker image. Ensure all dependencies are in `pyproject.toml`. |

### Secrets and Credentials

- **Never commit `.env`** — it contains database passwords and API keys.
- **CI/CD:** Add secrets to GitHub Settings > Secrets and Reference with `${{ secrets.SECRET_NAME }}` in workflows.
- **Local development:** If you must keep `.env` while committing other changes, use:
  ```bash
  git update-index --skip-worktree .env
  ```
  To revert: `git update-index --no-skip-worktree .env`

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming, code style, and PR guidelines.

---

<a name="العربية"></a>

## العربية

### نظرة عامة

**ETL لبيانات العملاء** هو مشروع Python محترف يعتمد على Docker ويدمج بيانات العملاء من مصادر متعددة (أنظمة CRM وملفات Excel)، ويقوم بتنظيفها وتحويلها، وإنتاج مجموعة بيانات جاهزة لمستودع البيانات للتحليل.

**مكدس التكنولوجيا:** Python 3.10+, Docker, docker-compose, pytest, pandas, pyodbc, python-dotenv, openpyxl

**أدوار الفريق:**
- استخراج البيانات (Data Extraction)
- تنظيف وتحويل البيانات (Data Cleaning & Transformation)
- نمذجة البيانات وتصميم المستودع (Data Modeling & Warehouse Design)
- التحقق من صحة البيانات والاختبار (Data Validation & Testing)
- التوثيق والعرض (Documentation & Presentation)

### البدء السريع مع Docker

جميع عمليات التطوير تتم داخل Docker. لا حاجة لتثبيت Python أو المكتبات على جهازك.

#### الإعداد

```bash
# 1. انسخ ملف البيئة من القالب
cp .env.template .env

# 2. عدّل .env ببيانات اعتماد قاعدة بيانات (اختياري للاختبار)
nano .env

# 3. بناء صورة Docker
docker compose build

# 4. تحقق من بيئتك داخل Docker
docker compose run --rm etl python -m etl_cli check_env

# 5. توليد بيانات وهمية للاختبار
docker compose run --rm etl python -m etl_cli generate_mock_data --rows 50 --seed 42
```

#### تشغيل الأوامر داخل Docker

```bash
# افتح shell تفاعلي داخل الحاوية
docker compose run --rm etl bash

# شغّل جميع الاختبارات
docker compose run --rm etl pytest

# فحص الأسلوب والقواعد
docker compose run --rm etl flake8 src tests

# فحص التنسيق
docker compose run --rm etl black --check src tests
```

### دورة حياة المشروع

- **المرحلة 1:** هيكل المشروع وإعداد بيئة Docker ✓
- **المرحلة 2:** توليد البيانات الوهمية والتحقق من البيئة
- **المرحلة 3:** فحوصات البيئة والأدوات التشخيصية
- **المرحلة 4:** تنفيذ خط أنابيب ETL والمنطق التجاري

### الترميز والسرية

- **لا تقم بالتزام `.env`** — يحتوي على كلمات مرور قاعدة البيانات ومفاتيح API.
- **CI/CD:** أضف الأسرار إلى GitHub Settings > Secrets.
- **التطوير المحلي:** إذا كنت بحاجة لـ `.env` مع التزام تغييرات أخرى:
  ```bash
  git update-index --skip-worktree .env
  ```

---

### License

MIT License — see [LICENSE](LICENSE) for details.
