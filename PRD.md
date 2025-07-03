Product Requirements Document (PRD)

Project codename: capstone-financeMaintainer(s): John Carlson (Product/Dev), open to core contributorsRepo URL: (to‑be‑created)License: MIT‑0 (MIT with no attribution, to maximise reuse)

1  Vision

Build an extensible, agent‑friendly Python toolkit that lets individuals, advisors, and autonomous LLM agents simulate personal‑finance decisions—retirement withdrawals, mortgage refinancing, large purchases, etc.—with academic‑quality rigor and production‑grade code. The toolkit must be:

Composable. New strategies, simulators, or data feeds drop in via plug‑ins—no fork required.

Deterministic. Given a seed + config, results are reproducible across machines.

Fast. 10 000 40‑year Monte‑Carlo paths in < 2 s on a modern laptop.

LLM‑native. Public APIs documented with machine‑readable DSPy signatures so Claude Code (or any agent) can reason about them.

2  Goals & Success Metrics

Goal

Metric

Target

Accurate retirement outputs

≤ 1 % error vs FIRECalc benchmarks on canonical cases

v1.0

Easy strategy plug‑in

≤ 20 code lines + 1 entry‑point to register

v1.0

Performance

10k×40yr paths < 2 s, P95

v1.0

LLM friendliness

All publics have Pydantic schemas + docstrings; pass dsp‑lint

continuous

Community traction

25 ⭐ & ≥ 3 external PRs

3 mo post‑launch

3  Personas

DIY Investor (Jane, 35): CLI + charts to compare refinance vs invest.

Financial Planner (Luis, CFP): Embeds library in Jupyter, exports PDF reports for clients.

LLM Agent (Claude): Reads repo/issues, autogenerates PRs to extend toolkit.

4  Functional Requirements

4.1  Core Engine /core

Market Simulator – Monte‑Carlo bootstrap, parametric (log‑normal), or external data feed.

Inflation Model – CPI bootstrap or user‑supplied series.

Cash‑Flow Ledger – tracks balances, taxes, fees on monthly or annual cadence.

Tax Module (stretch) – US Federal/State brackets, capital‑gain harvesting.

4.2  Strategy Plug‑ins /strategies

Each strategy = subclass of BaseStrategy with:

class BaseStrategy(ABC):
    def initial_withdrawal(self, state: YearState) -> float: ...
    def update_withdrawal(self, state: YearState) -> float: ...

Registered via entry_points.group="capstone_finance.strategies".

Bundled at v0.1:

4 % Rule (Bengen)

Constant Percentage

Endowment (Yale)

Guyton‑Klinger

Bundled at v0.2+: VPW, Floor‑Ceiling, Dynamic SWR, Guardrails v2.

4.3  Scenario Simulators /scenarios

RetirementSimulator – portfolio longevity & success metrics.

RefinanceAnalyzer – IRR, break‑even, NPVs.

BigPurchaseModeler – opportunity cost vs cash flow.

4.4  Interfaces

Interface

Tech

Notes

CLI

Typer

finance‑cli retire …

Python API

Importable modules

typed, docstring examples

DSPy Signatures

JSON schema under /signatures

keeps agents deterministic

Jupyter Notebook sample

examples/

for planners & data journalists

4.5  Reporting & Viz /reporting

Console tables via Rich.

Static charts: Matplotlib.  Interactive: Plotly (optional).

Results export: CSV, Parquet, or Feather.

4.6  Configuration & Persistence

YAML configs under /configs convertible to Pydantic models.

Seeded RNG for reproducibility (numpy.random.Generator).

Cache results in /outputs with ISO timestamp + hash.

5  Non‑Functional Requirements

Code Quality – black, ruff, mypy, pre‑commit hook; GitHub Actions block merges on failure.

Test Coverage ≥ 90 % – pytest + hypothesis (property‑based) for numerical stability.

Observability – built‑in logging (struct‑log), optional Sentry DSN.

Security – no secrets in repo, Dependabot on.

Financial Disclaimer – "for educational use, no fiduciary advice" banner in CLI & docs.

Accessibility – CLI colour auto‑disables if NO_COLOR env set.

6  Data Sources & Assumptions

Type

Default Source

Notes

Historical returns

Shiller S&P data via pandas‑datareader

fallback CSV snapshot for offline

Inflation

BLS CPI‑U

updated monthly cache

Yield curves (stretch)

FRED DGS10

for glidepath calcs

Assumptions live in /docs/assumptions.md and are version‑pinned.

7  Technical Stack

Layer

Choice

Why

Language

Python 3.12

pattern‑matching & perf

Data

Pandas, NumPy

industry std

Performance

Numba optional

vectorised Monte‑Carlo

Config & Validation

Pydantic v2

type‑safe

CLI

Typer

rich‑help

Docs

MkDocs‑Material + mkdocstrings

auto‑pull docstrings

Testing

pytest, hypothesis

robust maths

CI/CD

GitHub Actions

lint, test, publish to PyPI

8  High‑Level Architecture

financial‑toolkit/
├─ core/
│   ├─ market.py
│   └─ ledger.py
├─ strategies/
├─ scenarios/
├─ reporting/
├─ cli/
├─ signatures/
├─ configs/
├─ tests/
└─ docs/

strategies discovered at runtime via entry‑points → enables pip‑installable third‑party add‑ons.

9  Roadmap & Milestones

Milestone

Key Issues

ETA

🔧 Repo Scaffold + CI

#1‑#3

Week 1

📊 Core Engine v0.1

#4‑#8

Week 2

🏖 Retirement MVP

#9‑#15

Week 4

🏠 Refinance Analyzer

#16‑#20

Week 6

🛒 Big Purchase Modeler

#21‑#25

Week 7

📝 Docs + examples

#26‑#28

Week 8

🚀 v0.1 PyPI release

—

Week 8

10  Initial Issue Backlog (abridged)

Initialise repository, MIT‑0 licence, pre‑commit

Add GitHub Actions – lint + test matrix (3.12, 3.11)

Define data models – YearState, PortfolioParams, LoanParams

Implement MarketSimulator – bootstrap + log‑normal

Implement CashFlowLedger

Strategy base + 4 % Rule plug‑in

CLI retire command w/ CSV output

Unit tests for Strategy API

Add examples notebook & placeholder docs site

Add Dependabot + CodeQL workflow

11  Risks & Mitigations

Risk

Impact

Mitigation

Heavy computation slows agents

Poor UX

Vectorised code, optional Numba, --quick flag

Financial mis‑interpretation

User harm

Clear disclaimers, encourage consulting a CFP

LLM‑generated bugs

Prod breakage

Branch protection, CI, human review

Data feed outage

Simulation failure

Local CSV cache, allow user data load

12  Acceptance Criteria (MVP)

pip install financial‑toolkit installs without warnings.

finance‑cli retire --strategy 4percent --years 30 --seed 42 runs & writes summary CSV + PNG.

pytest -q passes; coverage ≥ 90 %.

Docs site build green; examples render.

One external user can add a new strategy with ≤ 20 LOC & docs.

Appendix A – Coding Standards & Contribution Guide (excerpt)

4‑space indent, Black‑formatted.

Type hints mandatory; mypy must pass.

Public functions require Google‑style docstrings with examples.

All CLI flags have tests in tests/cli/test_*.py.

Appendix B – LLM Integration Contract

All public callables annotated with @signature("name", in_=InputModel, out=OutputModel).

DSPy JSON manifests auto‑generated nightly to /signatures.

Breaking signature changes bump minor version.
