# Media Perception vs Reality

**A Data Engineering & Analysis Portfolio Project**

Exploring the disconnect between what kills us and what the media covers. This project analyzes causes of death in the US compared to their representation in media coverage (NYT, The Guardian) and public interest (Google searches).

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-0.9+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)

## Key Findings

| Cause | Deaths % | Media % | Gap |
|-------|----------|---------|-----|
| Terrorism | 0.01% | 33% | +33% (over-covered) |
| Homicide | 0.8% | 23% | +22% (over-covered) |
| Heart Disease | 28% | 3% | -25% (under-covered) |
| Cancer | 26% | 15% | -11% (under-covered) |

**Bottom line**: Violence gets 30x more coverage than it warrants. Chronic diseases that kill millions are virtually ignored.

## Project Structure

```
media-perception-reality/
├── src/
│   ├── extract/          # Data extraction (CSV loading)
│   │   └── loader.py
│   ├── transform/        # Data cleaning & enrichment
│   │   ├── cleaner.py    # Validation & cleaning
│   │   └── enricher.py   # Gap calculations, derived metrics
│   ├── load/             # Database operations
│   │   └── database.py   # DuckDB star schema
│   ├── pipeline.py       # Orchestrated ETL pipeline
│   └── analysis.py       # Analytical queries & insights
├── data/
│   ├── raw/              # Original CSV data
│   ├── processed/        # Cleaned intermediate files
│   └── media_perception.duckdb  # Analytical database
├── tests/                # pytest test suite
├── app.py                # Streamlit dashboard
└── requirements.txt
```

## Skills Demonstrated

### Data Engineering
- **ETL Pipeline**: Modular extract-transform-load architecture
- **Data Validation**: Schema validation, quality checks, data contracts
- **Data Modeling**: Star schema design (dimensions + facts)
- **Database**: DuckDB for analytical workloads
- **Testing**: Comprehensive pytest test suite
- **Logging**: Structured logging with loguru

### Data Analysis
- **Gap Analysis**: Quantifying perception vs reality
- **Trend Analysis**: Time-series patterns (pre/post 9/11)
- **Correlation**: Google searches vs media vs deaths
- **Statistical Aggregations**: Summary statistics by category

### Data Visualization
- **Interactive Dashboard**: Streamlit web application
- **Plotly Charts**: Bar charts, scatter plots, time series
- **Storytelling**: Insights with context and implications

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the ETL Pipeline

```bash
python -m src.pipeline
```

This will:
- Load raw CSV data
- Clean and validate
- Calculate coverage gaps
- Load into DuckDB database
- Save processed files

### 3. Launch the Dashboard

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### 4. Run Tests

```bash
pytest tests/ -v
```

## Data Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EXTRACT   │────▶│  TRANSFORM  │────▶│    LOAD     │────▶│   ANALYZE   │
│             │     │             │     │             │     │             │
│ - Load CSV  │     │ - Clean     │     │ - DuckDB    │     │ - Queries   │
│ - Validate  │     │ - Enrich    │     │ - Star      │     │ - Insights  │
│   schema    │     │ - Calculate │     │   Schema    │     │ - Dashboard │
│             │     │   gaps      │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Database Schema

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    dim_cause    │       │  fact_metrics   │       │    dim_year     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ cause_id (PK)   │──────▶│ cause_id (FK)   │◀──────│ year (PK)       │
│ cause_name      │       │ year (FK)       │       │ period          │
│ category        │       │ share_deaths    │       │ is_post_911     │
│ is_chronic      │       │ share_google    │       │ decade          │
│ is_violence     │       │ share_nyt       │       └─────────────────┘
└─────────────────┘       │ share_guardian  │
                          │ gap_media_avg   │
                          │ attention_score │
                          └─────────────────┘
```

## Key Metrics Explained

| Metric | Description |
|--------|-------------|
| `share_deaths` | % of total deaths from this cause |
| `share_nyt` | % of NYT articles covering this cause |
| `gap_media_avg` | Media coverage % minus deaths % |
| `attention_score` | Absolute value of gap (how distorted) |

**Positive gap** = Over-covered (more media than deaths warrant)
**Negative gap** = Under-covered (less media than deaths warrant)

## Sample Queries

```sql
-- Most over-covered causes
SELECT cause_name, ROUND(avg_gap, 1) as gap
FROM v_cause_summary
ORDER BY avg_gap DESC
LIMIT 5;

-- Heart disease coverage ratio
SELECT
    year,
    share_deaths,
    share_media_avg,
    ROUND(share_media_avg / share_deaths, 2) as coverage_ratio
FROM v_metrics_full
WHERE cause_name = 'Heart disease';
```

## Data Source

Dataset: [Causes of death vs. media coverage - Shen](https://github.com/owid/owid-datasets/tree/master/datasets/Causes%20of%20death%20vs.%20media%20coverage%20-%20Shen) (Our World in Data)

Data compiled by Owen Shen from:
- **Mortality**: CDC WONDER database
- **Google Trends**: Public interest data (2004+)
- **NYT**: Article database via API
- **The Guardian**: Open Platform API

Period: 1999-2016

## Why This Matters

Media coverage shapes public perception and policy priorities:

1. **Resource Allocation**: Funding follows fear, not facts
2. **Risk Perception**: People overestimate rare dramatic causes
3. **Policy Distortion**: Politicians respond to perceived threats

This project demonstrates how data can reveal hidden biases in information consumption.

## License

MIT License - Feel free to use for learning and portfolio purposes.

## Author

Allan Ninal - Data Engineer & Analyst

---

*Built with Python, DuckDB, Streamlit, and a passion for data-driven insights.*
