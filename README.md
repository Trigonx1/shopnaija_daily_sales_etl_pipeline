#    ShopNaija Daily Sales ETL Pipeline

> *Built by a junior data engineer and this project turns raw, messy e-commerce data into clean, analysis-ready reports — automatically, every single day.*

---

##  Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Tools and Technologies](#tools-and-technologies)
5. [Architecture and Pipeline Flow](#architecture-and-pipeline-flow)
6. [Step-by-Step Breakdown](#step-by-step-breakdown)
7. [Data Cleaning Decisions](#data-cleaning-decisions)
8. [Data Validation](#data-validation)
9. [How to Clone and Run the Project](#how-to-clone-and-run-the-project)
10. [Automation with Cron Job](#automation-with-cron-job)
11. [Sample Output](#sample-output)
12. [Struggles and Recommendations](#struggles-and-recommendations)

---

<br>

##  Project Overview

**ShopNaija** is a fast-growing Nigerian e-commerce platform selling electronics, fashion, and household goods across Lagos, Abuja, and Port Harcourt — think of it as a smaller, local version of Jumia.

This project is a fully automated **ETL (Extract, Transform, Load) data pipeline** built for ShopNaija using Python. Every morning at **7:00am**, the pipeline wakes up on its own and does the following:

-  **Extracts** yesterday's sales data from a CSV file, customer details from a Supabase database, and a live USD to Naira exchange rate from the internet
-  **Transforms** and cleans the raw data — fixes inconsistencies, removes bad rows, converts prices to Naira, and joins customer information to each sale
-  **Validates** the data to make sure it is healthy before saving
-  **Loads** the final clean report into a Supabase cloud database — ready for analysis

No button pressing. No manual work. The pipeline runs itself.

---

<br>

##  Problem Statement

ShopNaija's data lives in three completely separate places:

| Source | What it contains | The Problem |
|---|---|---|
| CSV file | Daily sales transactions | Dropped every morning by the sales team — inconsistent, has missing values and duplicates |
| Supabase database | Customer records | Stored separately — not connected to sales data |
| Exchange rate API | USD to NGN rate | All prices are in dollars — need live conversion to Naira for local reporting |

Without a pipeline to bring all three together, the business cannot:
- Track daily revenue in Naira
- Match sales to customer names and cities
- Produce a clean report for decision-making
- Do any of this automatically — someone would have to do it manually every single day

---

<br>

##  Objectives

The pipeline was built to achieve the following goals:

- Automatically read yesterday's sales CSV file without hardcoding any date
- Connect to the Supabase database and pull live customer records
- Fetch the live USD to Naira exchange rate from a free public API
- Clean and standardise the data — remove duplicates, handle missing values, fix column names
- Convert all prices from USD to Naira
- Merge the sales and customer datasets so each sale shows the customer's name, city, and loyalty tier
- Validate the data quality before saving
- Load the final clean dataset into a Supabase table called `daily_sales_report`
- Automate the whole process to run every day at 7:00am without any human action

---

<br>

##  Tools and Technologies

| Tool / Library | What it does in this project |
|---|---|
| **Python 3.x** | The main programming language everything is written in |
| **Pandas** | Reads CSV files, cleans data, merges tables — like Excel but in code |
| **psycopg2** | Connects Python to the PostgreSQL (Supabase) database to read customer data |
| **SQLAlchemy** | Saves the final clean DataFrame back into Supabase |
| **Requests** | Calls the exchange rate API — like visiting a website in Python |
| **JSON** | Saves the raw API response to a file before reading it back |
| **python-dotenv** | Reads database credentials from a secret `.env` file — keeps passwords safe |
| **Logging** | Records every step the pipeline takes with timestamps — like a diary |
| **OS / Datetime** | Creates folders, calculates yesterday's date automatically |
| **Supabase (PostgreSQL)** | Cloud database where customer records are stored and the final report is saved |
| **Cron Job** | Schedules the pipeline to run automatically every day at 7:00am |
| **Jupyter Notebook** | Used during development to test each function one at a time |
| **VS Code** | The code editor used to write and run the final script |
| **GitHub** | Where the code lives — version control and public portfolio |

---

<br>

##  Architecture and Pipeline Flow

This pipeline follows the classic **ETL** pattern — Extract, Transform, Load. Think of it like a factory conveyor belt:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTRACT                                     │
│                                                                     │
│    CSV File           Supabase DB          Exchange Rate API  │
│   (Sales data)         (Customers table)      (USD → NGN rate)      │
│                                                                     │
│   extract_sales()      extract_customers()    get_exchange_rate()   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TRANSFORM                                   │
│                                                                     │
│   transform()                                                       │
│                                                                     │
│   ✔ Standardise column names (lowercase, no spaces)                │
│   ✔ Fill missing quantity values with 0                            │
│   ✔ Fill missing prices with average price                         │
│   ✔ Drop rows where customer_id is missing                         │
│   ✔ Convert order_date to proper date format                       │
│   ✔ Merge sales with customer records (on customer_id)             │
│   ✔ Add total_amount_usd = quantity × unit_price_usd               │
│   ✔ Add total_amount_ngn = total_amount_usd × exchange rate        │
│   ✔ Remove all cancelled orders                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VALIDATE                                    │
│                                                                     │
│   validate()                                                        │
│                                                                     │
│   ✔ Check for any remaining null/empty values                      │
│   ✔ Check all quantities are greater than zero                     │
│   ✔ Check all prices are greater than zero                         │
│   ✔ Log warnings if checks fail (pipeline keeps running)           │
│   ✔ Return only the valid rows for loading                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           LOAD                                      │
│                                                                     │
│   load()                                                            │
│                                                                     │
│   ✔ Connect to Supabase using SQLAlchemy                           │
│   ✔ Insert final clean DataFrame into daily_sales_report table     │
│   ✔ Log success message with row count and exchange rate used      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTOMATE                                    │
│                                                                     │
│   Cron Job — runs pipeline every day at 7:00am automatically       │
└─────────────────────────────────────────────────────────────────────┘
```

---

<br>

##  Step-by-Step Breakdown

### Step 1 — Extract Sales CSV

The sales team drops a CSV file every morning named with the previous day's date — for example `sales_2026-04-06.csv`. The pipeline figures out yesterday's date automatically using Python's `datetime` and `timedelta` — it never hardcodes a date.

```python
today = datetime.today()
yesterday = today - timedelta(days=1)
date_str = yesterday.strftime('%Y-%m-%d')
SALES_FILE = f"sales_{date_str}.csv"
```

The `extract_sales()` function reads this file and returns it as a pandas DataFrame. If the file is missing, it logs an error and returns an empty table — the pipeline does not crash.

---

### Step 2 — Extract Customer Records

The `extract_customers()` function connects to the ShopNaija Supabase PostgreSQL database using `psycopg2`, runs a SQL query to fetch all customers, and returns the result as a DataFrame.

```python
conn = psycopg2.connect(host=..., port=..., database=..., user=..., password=...)
df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()
```

The connection is always closed after use — like hanging up the phone when the conversation is done.

---

### Step 3 — Fetch Exchange Rate

The `get_exchange_rate()` function visits a free public API that returns live exchange rates. The raw JSON response is saved to a file at `raw_data/api_raw/exchange_rate.json` before reading it back. This is good engineering practice — always save raw data before transforming it.

```python
response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
rate = data["rates"]["NGN"]
```

---

### Step 4 — Transform

The `transform()` function takes all three inputs and does all the cleaning work. See the [Data Cleaning Decisions](#data-cleaning-decisions) section below for details.

---

### Step 5 — Validate

The `validate()` function checks the data is healthy. It uses `if` statements — not `try/except` — exactly as the project requires. Warnings are logged but the pipeline always continues.

---

### Step 6 — Load

The `load()` function saves the final validated DataFrame into the `daily_sales_report` table in Supabase using SQLAlchemy's `to_sql()`. Using `if_exists="append"` means new rows are added on top of existing ones — historical data is preserved.

---

<br>

## 🧹 Data Cleaning Decisions

Every cleaning decision was made for a specific reason:

| What was cleaned | How it was handled | Why |
|---|---|---|
| Column names with uppercase or spaces | Converted to lowercase and stripped | Databases and Python don't like inconsistent naming — standardising prevents errors |
| Missing quantity values | Filled with 0 | Better than crashing — validation later flags these rows and removes them |
| Missing unit prices | Filled with the average price (mean imputation) | Prevents a crash while keeping the row — validation still checks if the result is valid |
| Rows with no customer_id | Dropped completely | Without a customer ID there is no way to match the sale to a customer — the row is useless |
| Date columns as plain text | Converted to proper datetime using `pd.to_datetime()` | Dates stored as text cannot be filtered or sorted properly in a database |
| Cancelled orders | Removed from the final table | Cancelled orders generate no revenue and should not appear in a daily sales report |
| Duplicate rows | Handled implicitly via dropna and merge — future improvement to add `drop_duplicates()` explicitly | Duplicates inflate sales figures and distort reporting |

---

<br>

##  Data Validation

Before any data is saved into Supabase, three checks are run inside the `validate()` function:

**Check 1 — No null values anywhere**
```python
if df.isnull().values.any():
    logging.warning("Null values detected")
```

**Check 2 — All quantities greater than zero**
```python
if (df["quantity"] <= 0).any():
    logging.warning("Invalid quantity detected")
```

**Check 3 — All prices greater than zero**
```python
if (df["unit_price_usd"] <= 0).any():
    logging.warning("Invalid price detected")
```

After the checks, only rows where both quantity AND price are valid are kept for loading:

```python
valid_df = df[(df["quantity"] > 0) & (df["unit_price_usd"] > 0)]
```

>  **Important:** Validation never stops the pipeline. It logs warnings and filters bad rows — but the pipeline always finishes running. This is how real production pipelines behave.

---

<br>

##  How to Clone and Run the Project

### Prerequisites
Make sure you have Python 3.x installed. You can check by running:
```bash
python --version
```

---

### Step 1 — Clone the Repository
```bash
git clone https://github.com/yourusername/shopnaija-etl-pipeline.git
cd shopnaija-etl-pipeline
```

---

### Step 2 — Create and Activate a Virtual Environment

**On Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

---

### Step 3 — Install Required Libraries
```bash
pip install -r requirements.txt
```

Or install them manually:
```bash
pip install pandas psycopg2-binary requests sqlalchemy python-dotenv
```

---

### Step 4 — Create Your `.env` File

Create a file called `.env` in the root of the project folder and add:

```
DB_HOST=aws-1-eu-north-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_username
DB_PASS=your_password
```

>  Never share this file or push it to GitHub. It is already listed in `.gitignore`.

---

### Step 5 — Add the Sales CSV File

Place the sales CSV file inside the `raw_data/` folder. The file must be named with yesterday's date:

```
raw_data/sales_2026-04-09.csv
```

---

### Step 6 — Run the Pipeline
```bash
python pipeline.py
```

You will see timestamped log messages in the terminal for every step. A log file called `shopnaija_pipeline.log` will also be created automatically.

---

### Project Folder Structure

```
shopnaija-etl-pipeline/
│
├── pipeline.py               ← main script
├── .env                      ← your secret credentials (never push to GitHub)
├── .gitignore                ← tells Git to ignore .env and log files
├── requirements.txt          ← list of libraries to install
├── shopnaija_pipeline.log    ← auto-generated log file
│
└── raw_data/
    ├── sales_2026-04-09.csv  ← drop your CSV file here
    └── api_raw/
        └── exchange_rate.json  ← saved automatically by the pipeline
```

---

<br>

##  Automation with Cron Job

A cron job is like setting an alarm clock for your Python script. Once configured, it runs the pipeline every day at 7:00am — no button pressing required.

### How to Set It Up (Mac/Linux)

**Step 1** — Open your terminal and type:
```bash
crontab -e
```

**Step 2** — A text editor opens. Add this line at the bottom:
```
0 7 * * * /usr/bin/python3 /full/path/to/pipeline.py
```

To find your full path, navigate into your project folder in the terminal and type `pwd`. Copy the result and add `/pipeline.py` at the end.

**Step 3** — Save and exit. Confirm it saved:
```bash
crontab -l
```

You should see your line listed. Take a screenshot of this for your submission.

### What `0 7 * * *` Means

| Field | Value | Meaning |
|---|---|---|
| Minute | 0 | At minute 0 (top of the hour) |
| Hour | 7 | At hour 7 (7am) |
| Day of month | * | Every day |
| Month | * | Every month |
| Day of week | * | Every day of the week |

Together: **run at exactly 7:00am, every single day.**

### On Windows — Use Task Scheduler

Windows does not have cron. Use **Task Scheduler** instead:

1. Search for "Task Scheduler" in the Start menu and open it
2. Click **Create Basic Task**
3. Name it `ShopNaija Pipeline`
4. Set the trigger to **Daily** at **7:00am**
5. Set the action to **Start a Program**
6. Program: `python`
7. Arguments: `C:\full\path\to\pipeline.py`
8. Click Finish

Take a screenshot of the task to include in your submission.

> 📷 **Screenshot placeholder** — Add your cron job or Task Scheduler screenshot here

---

<br>

##  Sample Output

### Terminal Log When Pipeline Runs Successfully

```
2026-04-13 19:18:19 - INFO - Pipeline started
2026-04-13 19:18:19 - INFO - Reading sales file: sales_2026-04-06.csv
2026-04-13 19:18:19 - INFO - Rows: 15, Columns: 8
2026-04-13 19:18:20 - INFO - Connecting to database...
2026-04-13 19:18:21 - INFO - Customers loaded: (6, 6)
2026-04-13 19:18:21 - INFO - Fetching exchange rate...
2026-04-13 19:18:21 - INFO - Raw API saved: raw_data/api_raw/exchange_rate.json
2026-04-13 19:18:21 - INFO - Exchange rate: 1362.35
2026-04-13 19:18:21 - INFO - Starting transformation...
2026-04-13 19:18:21 - INFO - Transformation complete: (13, 15)
2026-04-13 19:18:21 - INFO - Validating data...
2026-04-13 19:18:21 - INFO - 13 rows ready for loading
2026-04-13 19:18:21 - INFO - Loading data to database...
2026-04-13 19:18:22 - INFO - Loaded 13 rows successfully
2026-04-13 19:18:22 - INFO - Exchange rate used: 1362.35
2026-04-13 19:18:22 - INFO - Pipeline completed successfully
```

>  **Screenshot placeholder** — Add your Supabase `daily_sales_report` table screenshot here

---

<br>

##  Struggles and Recommendations

### What Was Hard

**1. The load error — `invalid literal for int() with base 10: 'None'`**

This was the trickiest bug. The pipeline ran successfully all the way through but failed at the very last step — loading into Supabase. The error came from a column that contained the text `"None"` (a string) instead of an actual empty value. Supabase tried to store it as an integer and failed.

The fix is to clean the DataFrame before loading — replace any remaining string `"None"` values with proper `NaN` (empty) values:

```python
import numpy as np
df = df.replace("None", np.nan)
```

Or alternatively, drop remaining null columns before loading.

**2. The psycopg2 UserWarning**

When reading from the database, this warning appeared:
```
UserWarning: pandas only supports SQLAlchemy connectable...
```
This means pandas prefers a SQLAlchemy engine instead of a raw psycopg2 connection for `pd.read_sql()`. To fix it properly, replace the psycopg2 connection in `extract_customers()` with a SQLAlchemy engine:

```python
engine = create_engine(DB_URL)
df = pd.read_sql("SELECT * FROM customers", engine)
```

**3. Understanding when `try/except` is appropriate vs plain `if`**

At first it was confusing why some functions use `try/except` and others use `if`. The rule is: use `try/except` for things that can fail because of the outside world — like a bad internet connection, wrong password, or missing file. Use `if` for data quality checks where you control the data and just want to log a warning.

**4. Managing missing values without losing too much data**

Deciding whether to drop a row or fill a missing value required thought. Dropping too aggressively loses data. Filling with the wrong value distorts analysis. The approach taken here — fill quantity with 0 and fill price with the average — is a reasonable beginner-level decision, but flagging these rows rather than silently filling them would be better in production.

---

### Recommendations for Next Steps

If I were to extend this project further, here is what I would add:

| Improvement | Why it matters |
|---|---|
| Replace string `"None"` values before loading | Fixes the load error encountered in this version |
| Use SQLAlchemy engine in `extract_customers()` | Removes the psycopg2 UserWarning |
| Add `drop_duplicates()` explicitly in `transform()` | The project brief requires it — currently handled implicitly |
| Add retry logic for the API call | If the internet is slow, one timeout should not kill the whole pipeline |
| Switch from `if_exists="append"` to `if_exists="replace"` with a date column | Prevents duplicate rows if the pipeline is accidentally run twice in one day |
| Use Apache Airflow instead of cron | Better scheduling, retry logic, monitoring dashboard, and error alerts |
| Store credentials in `.env` instead of hardcoding | Already done — but a future version should also mask passwords in logs |
| Add unit tests for each function | Catches bugs early — test that `transform()` always returns the right columns |

---

<br>

##  Author

Built by **Abdulbasit** — Junior Data Engineer.

 data engineering one pipeline at a time. Follow the journey on TikTok: **@asktrixx**

---

##  License

This project is open source and available under the MIT License.

