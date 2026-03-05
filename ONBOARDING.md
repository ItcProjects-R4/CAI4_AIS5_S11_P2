# 🎓 Onboarding Guide — دليل الانضمام للمشروع

## Customer Data ETL — ETL لبيانات العملاء من مصادر متعددة

**This guide is written for beginners.** If you have never used Git, Docker, or
worked on a team software project before, this guide will walk you through
everything you need. Read it from top to bottom the first time.

---

# Table of Contents

1. [Welcome to the Project](#1-welcome-to-the-project)
2. [What is ETL? (Explained Simply)](#2-what-is-etl-explained-simply)
3. [Project Structure Overview](#3-project-structure-overview)
4. [Required Tools — What to Install](#4-required-tools--what-to-install)
5. [Getting the Project on Your Computer](#5-getting-the-project-on-your-computer)
6. [Setting Up the Environment](#6-setting-up-the-environment)
7. [Running the Project with Docker](#7-running-the-project-with-docker)
8. [Running Project Tools](#8-running-project-tools)
9. [Team Roles](#9-team-roles)
10. [How to Start Contributing Code](#10-how-to-start-contributing-code)
11. [Understanding Pull Requests](#11-understanding-pull-requests)
12. [Running Tests](#12-running-tests)
13. [Common Mistakes and How to Avoid Them](#13-common-mistakes-and-how-to-avoid-them)
14. [Glossary — Key Terms Explained](#14-glossary--key-terms-explained)
15. [Getting Help](#15-getting-help)

---

# 1. Welcome to the Project

Hello! 👋 Welcome to the **Customer Data ETL** project.

You are about to work on a real data engineering project as part of a team.
This is a valuable learning opportunity — the skills you practice here (Python,
SQL, Docker, Git, teamwork) are the same skills used every day in the data
engineering industry.

## What does this project do?

In the real world, companies store customer data in many different places:

- A **CRM system** (Customer Relationship Management) — a database that stores
  customer names, emails, phone numbers, and registration dates.
- **Excel spreadsheets** — files with sales transactions, amounts, and product
  information.

The problem is: **the data is messy, scattered, and not ready for analysis.**

This project solves that problem. It:

1. **Collects** (extracts) customer data from those different sources.
2. **Cleans** (transforms) the data — removes duplicates, fixes errors, fills
   gaps.
3. **Stores** (loads) the clean data into a structured format ready for analysis
   and dashboards.

That three-step process is called **ETL**, which we explain next.

---

# 2. What Is ETL? (Explained Simply)

**ETL** stands for **Extract, Transform, Load**. Think of it like cooking:

| Step | Meaning | Cooking Analogy |
|------|---------|-----------------|
| **E**xtract | Get the raw data from its sources | Go to the market and buy ingredients |
| **T**ransform | Clean the data, fix errors, combine it | Wash, chop, and prepare the ingredients |
| **L**oad | Put the clean data into its final home | Cook the meal and serve it on a plate |

### A concrete example from our project

| Step | What happens |
|------|-------------|
| **Extract** | Read `crm_data.csv` (customer info) and `sales_data.xlsx` (sales transactions) from the `data/raw/` folder |
| **Transform** | Remove duplicate customers, validate email addresses, make sure all amounts are positive numbers |
| **Load** | Save the cleaned data into the `data/clean/` folder (and in the future, into a SQL Server database) |

### Why is this important?

Every company needs clean data to make decisions. If the data is messy, the
reports and dashboards will show wrong information. Data engineers build ETL
pipelines to make sure the data is always clean, consistent, and trustworthy.

**By completing this project, you will understand how real data pipelines
work.** This is one of the most in-demand skills in the tech industry.

---

# 3. Project Structure Overview

When you download this project, you will see many files and folders. Here is
what each one does:

```
customer-data-etl/                  ← The main project folder (root)
│
├── src/                            ← All Python source code lives here
│   └── etl_cli/                    ← The command-line tool for the pipeline
│       ├── __main__.py             ← Entry point — runs when you type: python -m etl_cli
│       ├── check_env.py            ← Checks if your environment is set up correctly
│       ├── generate_mock_data.py   ← Creates fake test data for development
│       ├── pipeline.py             ← The main ETL pipeline (extract → transform → load)
│       └── setup.py                ← Sets up the workspace for the first time
│
├── data/                           ← Data files go here
│   ├── raw/                        ← Raw (original, untouched) data
│   └── clean/                      ← Cleaned and transformed data (output)
│
├── sql/                            ← SQL scripts for database operations (future)
│
├── tests/                          ← Automated tests to verify code works correctly
│   ├── test_check_env.py           ← Tests for the environment checker
│   └── test_generate_mock_data.py  ← Tests for the mock data generator
│
├── docker/                         ← Docker configuration files
│   ├── Dockerfile                  ← Instructions to build the project container
│   └── entrypoint.sh               ← Script that runs when the container starts
│
├── .github/workflows/ci.yml       ← Automated testing on GitHub (CI/CD)
│
├── docker-compose.yml              ← Tells Docker how to run the project
├── Makefile                        ← Shortcuts for common commands (make build, etc.)
├── pyproject.toml                  ← Python project configuration and dependencies
├── .env.template                   ← Template for environment variables (passwords, etc.)
├── .gitignore                      ← Tells Git which files NOT to track
├── README.md                       ← Main project documentation
├── CONTRIBUTING.md                 ← Rules for contributing code
└── LICENSE                         ← Legal license (MIT — open source)
```

### Key folders to remember

| Folder | What you put there | Who works here |
|--------|--------------------|----------------|
| `src/etl_cli/` | Python code for the ETL pipeline | All developers |
| `data/raw/` | Input data (CSV, Excel files) | Extraction team |
| `data/clean/` | Output data (cleaned, ready for analysis) | Transformation team |
| `sql/` | Database table definitions and queries | Data Modeling team |
| `tests/` | Test files to verify code correctness | Validation team |

---

# 4. Required Tools — What to Install

Before you can work on this project, you need three tools on your computer.

## Tool 1: Git

### What is Git?

Git is a **version control system**. It tracks every change you make to the
code, so you can:

- See **what changed**, **when**, and **who** changed it.
- **Undo mistakes** by going back to a previous version.
- **Work as a team** without overwriting each other's code.

Think of Git like the "Track Changes" feature in Microsoft Word, but much more
powerful.

### How to install Git

- **Windows:** Download from https://git-scm.com/download/win and run the
  installer. Accept all default options.
- **macOS:** Open Terminal and type `git --version`. If it's not installed, macOS
  will prompt you to install it.
- **Linux (Ubuntu/Debian):** Open a terminal and run:
  ```bash
  sudo apt update
  sudo apt install git
  ```

### How to verify it's installed

Open a terminal (Command Prompt on Windows, Terminal on macOS/Linux) and type:

```bash
git --version
```

You should see something like:

```
git version 2.39.2
```

If you see an error like "command not found", Git is not installed correctly.

---

## Tool 2: Docker

### What is Docker?

Docker is a tool that creates **containers**. A container is like a tiny,
isolated computer running inside your computer.

Why do we use it?

- **Consistency:** Everyone on the team gets the exact same environment. No more
  "it works on my machine but not yours."
- **Safety:** Nothing you do inside the container affects your real computer.
- **Easy setup:** You don't need to install Python, pandas, or any other
  library on your computer. Docker installs everything automatically inside the
  container.

Think of it this way:

> 📦 A Docker container is like a lunchbox. Everything the project needs (Python,
> libraries, tools) is packed inside the box. You just open the box and start
> working.

### How to install Docker

- **Windows or macOS:** Download **Docker Desktop** from
  https://docs.docker.com/get-docker/ and run the installer.
  - On Windows, you may need to enable WSL 2 (Windows Subsystem for Linux).
    The Docker installer will guide you through this.
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update
  sudo apt install docker.io docker-compose-v2
  sudo usermod -aG docker $USER
  ```
  After running the last command, **log out and log back in** for the change to
  take effect.

### How to verify it's installed

```bash
docker --version
```

You should see something like:

```
Docker version 24.0.7
```

Also check Docker Compose:

```bash
docker compose version
```

You should see something like:

```
Docker Compose version v2.21.0
```

---

## Tool 3: Python (Optional)

### Why optional?

The project runs inside Docker, so you don't technically need Python on your
computer. However, having Python locally is useful if you want to:

- Read and understand Python files in your editor.
- Use your editor's autocomplete features.
- Run quick tests without starting Docker.

### How to install Python

- **Windows:** Download from https://www.python.org/downloads/ — make sure to
  check the box that says **"Add Python to PATH"** during installation.
- **macOS:** `brew install python3` (requires Homebrew) or download from
  python.org.
- **Linux:** Usually pre-installed. Check with `python3 --version`.

### How to verify it's installed

```bash
python3 --version
```

You should see something like:

```
Python 3.10.12
```

(Any version 3.10 or higher is fine.)

---

## Summary — Installation Checklist

Run all three commands. If all three work, you are ready to proceed.

```bash
git --version        # Should print a version number
docker --version     # Should print a version number
python3 --version    # Optional, but nice to have
```

✅ All showing version numbers? Great, move on to the next section.

❌ One of them gave an error? Go back and follow the installation steps for that
tool.

---

# 5. Getting the Project on Your Computer

## What is "cloning"?

The project code lives on GitHub (a website for storing code). To work on it,
you need to **download a copy** to your computer. In Git, downloading a project
is called **cloning**.

When you clone a project, you get:

- All the code files.
- The full history of every change ever made.
- A connection back to GitHub so you can share your work later.

## Step-by-step instructions

### Step 1: Open a terminal

- **Windows:** Open "Git Bash" (installed with Git) or "Command Prompt."
- **macOS / Linux:** Open "Terminal."

### Step 2: Navigate to where you want the project

Choose a folder on your computer where you keep your projects. For example:

```bash
cd ~/Learning
```

> 💡 **What does `cd` mean?** It stands for "change directory." It moves you
> into a different folder, like double-clicking a folder in File Explorer.

### Step 3: Clone the repository

Replace `<repository-url>` with the actual GitHub URL your team lead gave you:

```bash
git clone <repository-url>
```

For example:

```bash
git clone https://github.com/your-team/customer-data-etl.git
```

You will see output like:

```
Cloning into 'customer-data-etl'...
remote: Enumerating objects: 85, done.
remote: Counting objects: 100% (85/85), done.
Receiving objects: 100% (85/85), 25.00 KiB | 500.00 KiB/s, done.
```

### Step 4: Enter the project folder

```bash
cd customer-data-etl
```

### Step 5: Verify you are in the right place

```bash
ls
```

> 💡 **What does `ls` mean?** It stands for "list." It shows all files and
> folders in the current directory. On Windows Command Prompt, use `dir` instead.

You should see files like `README.md`, `Makefile`, `docker-compose.yml`, `src/`,
etc.

**Congratulations!** 🎉 The project is now on your computer.

---

# 6. Setting Up the Environment

## What are "environment variables"?

Some information (like database passwords) should **never** be written directly
in the code. Instead, we store them in a special file called `.env` (pronounced
"dot env").

The `.env` file contains **key=value** pairs like:

```
DB_SERVER=localhost,1433
DB_PASSWORD=MySecretPassword123
```

The program reads these values at runtime, so the actual passwords never appear
in the source code.

## Why is this important?

If someone accidentally uploads passwords to GitHub, **anyone in the world
could see them**. That's a serious security risk. The `.env` file is listed in
`.gitignore`, which tells Git to **never track it**, so it can never be
accidentally uploaded.

## Step-by-step: Create your `.env` file

### Step 1: Copy the template

```bash
cp .env.template .env
```

> 💡 **What does `cp` mean?** It stands for "copy." This command copies the file
> `.env.template` and creates a new file called `.env`.

### Step 2: Open the `.env` file in a text editor

```bash
nano .env
```

Or open it in VS Code:

```bash
code .env
```

### Step 3: Review the contents

You will see something like this:

```ini
# Database Configuration / إعدادات قاعدة البيانات
DB_SERVER=localhost,1433
DB_NAME=customer_data_etl
DB_USER=sa
DB_PASSWORD=YourSecurePasswordHere123!

# Application Environment / بيئة التطبيق
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

For now, **you do not need to change anything**. The default values are fine for
development with mock (fake) data. If your team provides real database
credentials later, you will update them here.

### Step 4: Save and close

- In `nano`: press `Ctrl + O`, then `Enter` to save, then `Ctrl + X` to exit.
- In VS Code: press `Ctrl + S` to save.

## ⚠️ The Golden Rule

> **Never commit the `.env` file to Git.**
>
> The `.env` file contains sensitive information (passwords, API keys). It must
> stay on your computer only. The `.gitignore` file is already configured to
> prevent this, but always double-check.

If Git ever asks you to add `.env`, say **no**.

---

# 7. Running the Project with Docker

This is where Docker shines. Instead of installing Python, pandas, and dozens
of other tools on your computer, you will build a Docker **container** that has
everything pre-installed.

## What is a Docker Container? (Simple explanation)

Imagine you have a box 📦. Inside the box:

- Python 3.10 is installed
- All project libraries (pandas, pytest, etc.) are installed
- The project code is inside

When you "start the container," it's like opening the box and stepping inside
a tiny computer that has everything ready. When you're done, you close the box.
Nothing you did inside the box affects your real computer.

## Step-by-step: Build and run the container

### Step 1: Make sure Docker is running

- **Windows / macOS:** Open the Docker Desktop application. Wait until it says
  "Docker is running" (green icon in the system tray).
- **Linux:** Docker usually runs automatically. Verify with:
  ```bash
  docker info
  ```
  If you see an error, start Docker with `sudo systemctl start docker`.

### Step 2: Build the Docker image

From the project folder (`customer-data-etl/`), run:

```bash
docker compose build
```

> 💡 **What does this do?** It reads the `Dockerfile` (a recipe file) and builds
> a Docker image. An "image" is like a snapshot of the tiny computer. This step
> may take 2-3 minutes the first time because it downloads Python and installs
> all libraries. Subsequent builds are much faster.

You will see output like:

```
 => [internal] load build definition from Dockerfile
 => [1/6] FROM docker.io/library/python:3.10-slim
 => [3/6] RUN apt-get update ...
 => [5/6] RUN pip install ...
 => => writing image sha256:abc123...
```

When it finishes without errors, the image is built. ✅

### Step 3: Open an interactive shell inside the container

```bash
docker compose run --rm etl bash
```

> 💡 **What does this do?**
>
> - `docker compose run` — Start a container using the settings in
>   `docker-compose.yml`.
> - `--rm` — Automatically delete the container when you exit (keeps things
>   clean).
> - `etl` — The name of the service defined in `docker-compose.yml`.
> - `bash` — Open a Bash shell (a command-line interface) inside the container.

You will see a new prompt like:

```
etl@abc123:/app$
```

This means you are **inside the container**. Everything you type now runs inside
the container, not on your personal computer.

### Step 4: Try some commands inside the container

```bash
python --version          # Should show: Python 3.10.x
pip list                  # Shows all installed Python packages
ls                        # Shows project files
```

### Step 5: Exit the container

When you're done, type:

```bash
exit
```

This closes the container and returns you to your normal terminal.

### Using Makefile shortcuts

The project includes a `Makefile` with shortcuts so you don't have to type long
commands:

| What you type | What it does |
|---------------|-------------|
| `make build` | Builds the Docker image |
| `make shell` | Opens a shell inside the container |
| `make test` | Runs all tests |
| `make lint` | Checks code style |
| `make fmt` | Formats code automatically |
| `make clean` | Deletes generated data files |

For example, instead of `docker compose run --rm etl bash`, you can just type:

```bash
make shell
```

Much easier!

---

# 8. Running Project Tools

The project includes several built-in tools you can run inside the Docker
container. Here is what each one does and how to run it.

## Tool 1: Check Environment

This tool verifies that everything is set up correctly.

```bash
docker compose run --rm etl python -m etl_cli check-env
```

Or using Make:

```bash
make check-env
```

**What it checks:**

- ✓ Python version is 3.10 or higher
- ✓ Required packages (pandas, openpyxl, etc.) are installed
- ✓ Environment variables are set (from your `.env` file)
- ✓ ODBC drivers are available (for database connections)

**Example output:**

```
🔍 Checking environment...

✓ Python 3.10
✓ typer installed
✓ dotenv installed
✓ pandas installed
✓ openpyxl installed

✓ .env file loaded
  ✓ DB_SERVER=loc***
  ✓ DB_NAME=cus***
  ✓ DB_USER=s***
  ✓ DB_PASSWORD=***

============================================================
✅ All checks passed! Environment is ready.
```

> 💡 Notice that passwords are **masked** (shown as `***`). The tool never
> prints real passwords to the screen.

---

## Tool 2: Generate Mock Data

This tool creates **fake (mock) data** for testing. You don't need a real
database to start developing.

```bash
docker compose run --rm etl python -m etl_cli generate-mock-data --rows 50 --seed 42
```

Or using Make:

```bash
make mock-data
```

> 💡 **What is `--seed 42`?** A "seed" is a starting number for the random
> generator. If everyone uses `--seed 42`, everyone gets the **exact same fake
> data**. This makes it easy to compare results and write tests.

**What it creates:**

| File | Contents |
|------|----------|
| `data/raw/crm_data.csv` | 50 fake customers (name, email, phone, country, registration date) |
| `data/raw/sales_data.xlsx` | 50 fake sales transactions (customer ID, amount, date, product name) |

**Example output:**

```
🌱 Generating mock data (seed=42, rows=50)...

✓ Generated 50 CRM records
✓ Generated 50 sales transactions
✓ Wrote data/raw/crm_data.csv (50 rows)
✓ Wrote data/raw/sales_data.xlsx (50 rows)

✅ Mock data generated successfully!
```

After running this, open `data/raw/crm_data.csv` to see the fake customer data.

---

## Tool 3: Run the ETL Pipeline

This runs the full ETL process (extract → transform → load).

```bash
docker compose run --rm etl python -m etl_cli run-pipeline
```

> ⚠️ **Note:** Right now, the pipeline contains **placeholder code** (stubs).
> The team will implement the real logic during the project. Running it will
> show what *would* happen at each step.

**Example output:**

```
🔄 Starting ETL Pipeline...

📥 Extract phase...
  ✓ Found data/raw/crm_data.csv
  ✓ Found data/raw/sales_data.xlsx
  ✓ Extraction complete

⚙️  Transform phase...
  • Deduplicate customer records (placeholder)
  • Validate email addresses (placeholder)
  ✓ Transformation complete

📤 Load phase...
  • Would write to data/clean/customer_dim.csv (placeholder)
  ✓ Load complete

✅ Pipeline complete!
```

---

## Tool 4: Clean Up

This removes generated data files so you can start fresh.

```bash
docker compose run --rm etl python -m etl_cli clean
```

Or using Make:

```bash
make clean
```

---

## Summary of Commands

| Command | What it does |
|---------|-------------|
| `make build` | Build the Docker image |
| `make shell` | Open shell inside the container |
| `make check-env` | Verify environment setup |
| `make mock-data` | Generate fake test data |
| `make test` | Run automated tests |
| `make lint` | Check code for style issues |
| `make fmt` | Auto-format code |
| `make clean` | Delete generated data files |

---

# 9. Team Roles

This project is designed for a team of 5 people, each with a specific role.
Here is what each role does.

## Role 1: Extraction Engineer (مهندس استخراج البيانات)

**Your job:** Get data from its sources and bring it into the project.

**What you work on:**

- Reading data from CSV files and Excel spreadsheets
- Connecting to databases (SQL Server) and running queries
- Writing code in `src/etl_cli/pipeline.py` (the `extract()` function)

**Skills you will practice:** pandas, pyodbc, file I/O, SQL

---

## Role 2: Transformation Engineer (مهندس تنظيف وتحويل البيانات)

**Your job:** Clean the raw data and make it consistent.

**What you work on:**

- Removing duplicate records
- Handling missing values (empty cells)
- Validating data formats (e.g., email addresses, phone numbers)
- Writing transformation code in `src/etl_cli/pipeline.py` (the `transform()`
  function)

**Skills you will practice:** pandas, data cleaning, regular expressions

---

## Role 3: Data Modeling Engineer (مهندس نمذجة البيانات وتصميم المستودع)

**Your job:** Design the final database structure.

**What you work on:**

- Designing dimension tables (e.g., `dim_customer`) and fact tables
  (e.g., `fact_transaction`)
- Writing SQL scripts in the `sql/` folder
- Defining the schema (columns, data types, relationships)

**Skills you will practice:** SQL, database design, star schema

---

## Role 4: Validation & Testing Engineer (مهندس التحقق والاختبار)

**Your job:** Make sure the data is correct and the code works.

**What you work on:**

- Writing tests in the `tests/` folder
- Verifying data quality (no nulls where there shouldn't be, correct counts)
- Running `make test` to ensure all tests pass
- Checking edge cases (what happens with empty files, missing columns)

**Skills you will practice:** pytest, data validation, testing strategies

---

## Role 5: Documentation & Presentation Engineer (مهندس التوثيق والعرض)

**Your job:** Write clear documentation and prepare the final presentation.

**What you work on:**

- Updating `README.md` and other documentation files
- Writing comments and docstrings in the code
- Preparing diagrams showing the data flow
- Creating the final project presentation

**Skills you will practice:** technical writing, communication, Markdown

---

## Important: Communication

- **Talk to each other regularly.** Use your team chat, meet in person, or have
  video calls.
- **Review each other's code.** When someone creates a Pull Request (explained
  below), at least one other team member should review it.
- **Ask questions.** If you don't understand something, ask. Every team member
  was a beginner once.
- **Share progress.** Let the team know what you're working on so efforts
  don't overlap.

---

# 10. How to Start Contributing Code

This section explains the Git workflow step by step. Follow it every time you
want to make changes to the project.

## What is a "branch"?

Think of the project code as a tree 🌳. The main trunk is called `main` — it
contains the latest working version of the project.

When you want to make changes, you create a **branch** — a copy of the code
that you can modify without affecting the main trunk. When your changes are
ready, you **merge** your branch back into `main`.

This way, everyone can work on different features at the same time without
breaking each other's code.

```
main:          ─────────────────────────────── ← stable code
                    \                    /
feature/add-email:   ──────────────────  ← your work happens here
```

## Step-by-step workflow

### Step 1: Make sure you have the latest code

Before starting any new work, always get the latest changes from the team:

```bash
git pull origin main
```

> 💡 **What does this do?** It downloads the latest changes from GitHub and
> updates your local copy of `main`.

### Step 2: Create a new branch

```bash
git checkout -b feature/my-feature-name
```

> 💡 **What does this do?**
>
> - `git checkout -b` — Create a new branch AND switch to it.
> - `feature/my-feature-name` — The name of your branch. Use a descriptive name
>   that tells others what you're working on.

**Branch naming examples:**

| Good name ✅ | Bad name ❌ |
|-------------|------------|
| `feature/add-email-validation` | `my-branch` |
| `feature/extract-crm-data` | `test123` |
| `fix/duplicate-customers` | `branch1` |

### Step 3: Make your changes

Open the relevant file in your code editor (e.g., VS Code) and make your
changes. For example, if you're the Transformation Engineer, you might edit
`src/etl_cli/pipeline.py`.

### Step 4: Check what you changed

```bash
git status
```

This shows a list of files you modified, added, or deleted. Example output:

```
On branch feature/add-email-validation
Changes not staged for commit:
        modified:   src/etl_cli/pipeline.py

Untracked files:
        src/etl_cli/validators.py
```

### Step 5: Stage your changes

```bash
git add .
```

> 💡 **What does "staging" mean?** Before you save (commit) your changes, you
> need to tell Git which files to include. `git add .` adds **all** changed
> files. You can also add specific files:
>
> ```bash
> git add src/etl_cli/pipeline.py
> ```

### Step 6: Commit your changes

```bash
git commit -m "Add email validation to transform phase"
```

> 💡 **What is a "commit"?** A commit is like taking a snapshot of your code at
> this moment. The message after `-m` describes what you changed. Write clear,
> descriptive messages.

**Good commit messages ✅:**

- `"Add email validation to transform phase"`
- `"Fix duplicate customer bug in extract"`
- `"Add unit tests for mock data generator"`

**Bad commit messages ❌:**

- `"update"`
- `"fix"`
- `"asdfg"`

### Step 7: Push your branch to GitHub

```bash
git push origin feature/my-feature-name
```

> 💡 **What does this do?** It uploads your branch to GitHub so the team can
> see your work.

If this is the first time you're pushing this branch, Git might ask you to set
it up. Use the command it suggests, which is usually the same as above.

---

# 11. Understanding Pull Requests

## What is a Pull Request (PR)?

A **Pull Request** (also called a "PR" or "merge request") is a way to ask the
team: *"Please review my changes and merge them into the main code."*

It's like raising your hand in class and saying: *"I made some changes. Can
someone check if they're correct before we add them to the project?"*

## How to create a Pull Request

### Step 1: Go to your repository on GitHub

Open a web browser and go to your project's GitHub page.

### Step 2: You will see a yellow banner

After you push a branch, GitHub shows a banner like:

> **"feature/add-email-validation" had recent pushes — Compare & pull request**

Click the **"Compare & pull request"** button.

### Step 3: Fill in the details

- **Title:** A short summary of what you did.
  Example: `"Add email validation to transform phase"`

- **Description:** Explain your changes in more detail:
  - What did you change?
  - Why did you change it?
  - How can someone test it?

Example description:

```
## What I changed
- Added email validation function in pipeline.py
- Emails without @ are now flagged as invalid
- Added 3 unit tests for the validation function

## How to test
1. Run: docker compose run --rm etl pytest tests/test_pipeline.py
2. All 3 new tests should pass
```

### Step 4: Request a review

On the right side, click "Reviewers" and select a team member. They will look
at your code and either:

- **Approve** it ✅ — Your changes are ready to be merged.
- **Request changes** 🔄 — They found something to fix. Read their comments,
  make the fixes on your branch, commit, and push again. The PR updates
  automatically.

### Step 5: Merge

Once a team member approves, click **"Merge pull request"**. Your changes are
now part of `main`! 🎉

### Step 6: Clean up

After merging, delete your feature branch (GitHub offers a button for this).
Then on your local computer:

```bash
git checkout main
git pull origin main
```

This switches you back to `main` and downloads the merged changes.

---

# 12. Running Tests

## What are tests?

Tests are small programs that **automatically check** if your code works
correctly. Instead of manually running the program and checking the output with
your eyes, tests do it for you in seconds.

## Why are tests important?

- **Catch bugs early** — Before your code is merged, tests verify it works.
- **Prevent regressions** — When someone changes code later, tests make sure
  they didn't accidentally break something that was working before.
- **Save time** — Running 25 tests takes 2 seconds. Manually checking everything
  would take 30 minutes.

## How to run tests

### Run all tests

```bash
docker compose run --rm etl pytest
```

Or:

```bash
make test
```

**Example output (all tests pass):**

```
========================= test session starts ==========================
collected 25 items

tests/test_check_env.py ......                                    [ 24%]
tests/test_generate_mock_data.py ...................              [100%]

========================= 25 passed in 1.23s ===========================
```

Each dot (`.`) means one test passed. If a test fails, you'll see an `F` and
a detailed error message showing what went wrong.

### Run a specific test file

```bash
docker compose run --rm etl pytest tests/test_check_env.py
```

### Run tests with more detail

```bash
docker compose run --rm etl pytest -v
```

The `-v` flag means "verbose" — it shows the name of each test.

## How to write a test (example)

Tests live in the `tests/` folder. Here's a simple example:

```python
# tests/test_example.py

def test_addition():
    """Test that 2 + 2 equals 4."""
    result = 2 + 2
    assert result == 4   # If this is True, the test passes

def test_name_is_not_empty():
    """Test that a customer name is not an empty string."""
    name = "Ahmed"
    assert len(name) > 0  # If the name has characters, this passes
```

The `assert` keyword checks if something is true. If it's true, the test
passes ✅. If it's false, the test fails ❌ and tells you exactly what went
wrong.

---

# 13. Common Mistakes and How to Avoid Them

## Mistake 1: Editing code on the `main` branch

❌ **Never make changes directly on `main`.**

✅ Always create a feature branch first:

```bash
git checkout -b feature/my-change
```

## Mistake 2: Committing the `.env` file

❌ The `.env` file contains passwords. It must **never** be uploaded to GitHub.

✅ The project's `.gitignore` already prevents this. But if Git ever asks you to
add `.env`, say no:

```bash
# DON'T DO THIS:
git add .env       # ← NEVER

# DO THIS INSTEAD:
git add src/       # ← Only add source code files
```

## Mistake 3: Forgetting to pull before starting work

If you don't get the latest code before starting, your changes might conflict
with someone else's work.

✅ Always start your day with:

```bash
git checkout main
git pull origin main
git checkout -b feature/new-work
```

## Mistake 4: Writing unclear commit messages

❌ `git commit -m "stuff"`

✅ `git commit -m "Add phone number validation to customer records"`

## Mistake 5: Not running tests before pushing

Always verify your code works before sharing it:

```bash
make test
```

If any tests fail, fix the issue before pushing.

## Mistake 6: Running commands on your computer instead of in Docker

Most project commands should run **inside the Docker container**, not on your
host computer. If you see errors about missing modules like `pandas` or `pyodbc`,
make sure you're running inside Docker:

```bash
# ✅ Correct — runs inside Docker
docker compose run --rm etl pytest

# ❌ Incorrect — runs on your computer (might not have pandas installed)
pytest
```

---

# 14. Glossary — Key Terms Explained

Here are important terms you will encounter. Refer back to this section any
time you see an unfamiliar word.

| Term | Meaning |
|------|---------|
| **Repository (repo)** | A folder tracked by Git that contains all project files and their history. Think of it as the project's home. |
| **Clone** | Download a copy of a repository from GitHub to your computer. |
| **Branch** | A separate copy of the code where you make changes without affecting the main version. Like a sandbox for your work. |
| **Commit** | A snapshot of your code at a specific point in time, with a message describing what changed. |
| **Push** | Upload your commits from your computer to GitHub. |
| **Pull** | Download the latest changes from GitHub to your computer. |
| **Pull Request (PR)** | A request to merge your branch into `main`. Team members review your code before it's merged. |
| **Merge** | Combine the changes from one branch into another (usually into `main`). |
| **Main (branch)** | The primary branch containing the latest stable version of the project. |
| **Docker** | A tool that creates isolated containers to run software consistently on any computer. |
| **Container** | A lightweight, isolated environment (like a tiny virtual computer) created by Docker. |
| **Image** | A blueprint for a container. Built from a `Dockerfile`. You build the image once, then create containers from it. |
| **ETL** | Extract, Transform, Load — a process to move and clean data from sources to a destination. |
| **Pipeline** | A series of automated steps that process data from start to finish. |
| **CSV** | Comma-Separated Values — a simple file format for spreadsheet data. Can be opened in Excel or Google Sheets. |
| **XLSX** | An Excel file format. |
| **pandas** | A Python library for working with tables of data (like a programmable Excel). |
| **pyodbc** | A Python library for connecting to databases like SQL Server. |
| **pytest** | A Python tool for running automated tests. |
| **`.env` file** | A file containing environment variables (like passwords) that should never be uploaded to GitHub. |
| **`.gitignore`** | A file that tells Git which files to ignore and never track. |
| **Makefile** | A file containing shortcuts for commonly used commands (e.g., `make test`). |
| **Terminal** | The text-based interface where you type commands. Also called "command line," "shell," or "console." |
| **Lint / Linter** | A tool that checks your code for style issues and potential errors without running it. |
| **CI/CD** | Continuous Integration / Continuous Delivery — automated processes that test and deploy code when you push to GitHub. |
| **SQL** | Structured Query Language — a language for managing and querying databases. |
| **Data Warehouse** | A database designed for analysis and reporting, organized in a specific structure (like star schema). |
| **Star Schema** | A database design pattern with a central "fact" table (transactions) surrounded by "dimension" tables (customers, products, dates). |
| **Mock Data** | Fake data generated for testing purposes, so you don't need access to real databases during development. |

---

# 15. Getting Help

## If you're stuck with Git

```bash
git status        # See what's going on
git log --oneline # See recent commits
git diff          # See what you changed
```

If you made a mistake and want to **undo your last commit** (before pushing):

```bash
git reset --soft HEAD~1
```

This undoes the commit but keeps your changes so you can fix them.

## If you're stuck with Docker

```bash
docker compose ps          # See running containers
docker compose down        # Stop everything
docker compose build       # Rebuild the image (fixes most issues)
```

If nothing works, try removing everything and starting fresh:

```bash
docker compose down -v     # Stop and remove all containers and volumes
docker compose build       # Rebuild from scratch
```

## If you're stuck with the code

1. **Read the error message carefully.** Python error messages tell you the
   exact file and line number where the problem is.
2. **Search the error message online.** Copy the last line of the error and
   paste it into Google. You'll often find answers on Stack Overflow.
3. **Ask your team.** Post the error message in your team chat. Someone might
   have seen the same issue.
4. **Ask your instructor.** If the team can't solve it, bring it to your
   instructor with the full error message and what you've tried.

## Useful resources

| Resource | Link |
|----------|------|
| Git tutorial for beginners | https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control |
| Docker getting started | https://docs.docker.com/get-started/ |
| Python pandas tutorial | https://pandas.pydata.org/docs/getting_started/intro_tutorials/ |
| pytest documentation | https://docs.pytest.org/en/stable/getting-started.html |

---

# Quick Reference Card

Print this or keep it open while you work:

```
╔══════════════════════════════════════════════════════════════════════╗
║                   CUSTOMER DATA ETL — CHEAT SHEET                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  FIRST-TIME SETUP                                                  ║
║  ───────────────                                                   ║
║  git clone <url>                    Download the project            ║
║  cd customer-data-etl              Enter the folder                 ║
║  cp .env.template .env             Create environment file          ║
║  docker compose build              Build the Docker image           ║
║                                                                    ║
║  DAILY WORKFLOW                                                    ║
║  ──────────────                                                    ║
║  git pull origin main              Get latest code                  ║
║  git checkout -b feature/my-work   Create a new branch              ║
║  (make your changes)                                               ║
║  make test                         Run tests                        ║
║  git add .                         Stage your changes               ║
║  git commit -m "description"       Save a snapshot                  ║
║  git push origin feature/my-work   Upload to GitHub                 ║
║  → Create Pull Request on GitHub                                   ║
║                                                                    ║
║  USEFUL COMMANDS                                                   ║
║  ───────────────                                                   ║
║  make shell                        Open shell in Docker             ║
║  make test                         Run tests                        ║
║  make lint                         Check code style                 ║
║  make mock-data                    Generate test data               ║
║  make check-env                    Verify environment               ║
║  make clean                        Delete generated files           ║
║                                                                    ║
║  GIT HELP                                                          ║
║  ────────                                                          ║
║  git status                        Show what changed                ║
║  git log --oneline                 Show recent commits              ║
║  git diff                          Show detailed changes            ║
║                                                                    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

**You're ready to start!** 🎉

If you followed this guide from top to bottom, you now know:

- ✅ What ETL means and why it matters
- ✅ How to navigate the project structure
- ✅ How to install and use Git, Docker, and Python
- ✅ How to clone the project and set up your environment
- ✅ How to use Docker to run the project
- ✅ How to run tests and project tools
- ✅ What your role on the team is
- ✅ How to contribute code using branches and Pull Requests
- ✅ How to avoid common mistakes

Welcome aboard, and happy coding! 🚀

---

*This guide was created for the Customer Data ETL project (ETL لبيانات العملاء
من مصادر متعددة). If anything is unclear, please open a GitHub issue or
ask your team.*
