Parity: complete build plan

I assumed about 20 hours/week (part-time), Oracle → PostgreSQL, and a goal of portfolio first, consulting or pilots second. If you can work full-time (40 hrs/week), halve every duration. If your goal is different, only Phase 5 changes.

Phase 0: Validate and prepare (weeks -2 to 0)
Task	Output
Talk to 3-5 data engineers or migration consultants (LinkedIn, r/dataengineering, local meetups). Ask: “What breaks most when you migrate Oracle/Teradata SQL? How do you prove results match?”	One page of notes. Confirms or changes your dialect pair
Skills self-check: rate yourself on Oracle SQL/PL/SQL, PostgreSQL, Python, Docker, LangGraph	A ramp-up list, and 2 to 3 weeks added to the schedule if you’re weak on any
Check the name “Parity” (GitHub, PyPI, domain, trademark). Fallback: SQLParity	Name locked, repo created
Pick a license (MIT or Apache-2.0 for code) and note the licenses of each dataset you’ll use	LICENSE and DATA_SOURCES.md
Set up tracking: a private notes doc, a GitHub Project board, and a spreadsheet for time and cost	Weekly review habit

Gate 0: at least 2 people confirm the problem is real. If nobody does, switch to the second-ranked idea before spending months.

Phase 1: Foundation (weeks 1-6)
Week	Work	Done when
1	Install Docker, Python 3.11+, Git. Create repo layout. Write docker-compose.yml with Oracle Free and Postgres. Load Oracle’s HR schema	docker compose up gives both databases, queryable
2	Build the corpus: TPC-H/TPC-DS queries rewritten for Oracle, HR/SH schema queries, SQL from open-source repos. Generate edge-case data with Faker (NULLs, '', leap days, unicode, boundary numbers)	100+ objects committed, licenses recorded
3	Baseline: sqlglot-only conversion across the corpus, executed on both databases	First honest pass rate, saved as bench/results/baseline.json
4	Verification layer 1-3: compile on target, schema/type match, row counts	A deliberately planted mismatch gets caught
5	Verification layer 4-5: column aggregates and row-level hashing with configurable tolerances (for example decimals within 1e-9)	Mismatches report which rows/columns differ, without dumping raw data
6	Benchmark runner: one command re-runs everything and writes a results table. Add CI (GitHub Actions) to run a small subset	Every change gives a before/after number

Gate 1 (end of week 6): baseline measured, verifier catches planted bugs, benchmark reproducible. If sqlglot alone already passes nearly everything on your corpus, your corpus is too easy, so add harder objects (hierarchical queries, analytic functions, MERGE, date arithmetic).

Phase 2: Intelligence (weeks 7-12)
Week	Work	Done when
7	Knowledge base v1: 20+ Oracle→Postgres differences in dialect_differences.yaml (empty string as NULL, DATE has a time part, ROWNUM, CONNECT BY, DECODE, NVL, (+) joins, sequences, TRUNC on dates, string comparison and padding). Each gets a failing test	SEMANTIC_DIFFERENCES.md published
8	LLM provider wrapper: Ollama (local) and one hosted API, per-call and per-object cost caps, response caching, retry limits	Caps tested to actually stop a runaway loop
9	Repair loop in LangGraph: analyze → convert → verify → repair (max 3 attempts). The model receives the mismatch summary plus relevant KB entries, never raw rows	Pass rate rises over baseline on the same corpus
10	Ablation study: sqlglot only vs. +LLM vs. +LLM+KB. Log failure categories	Table showing what each component contributes
11	Evidence reports: per-object HTML (source SQL, converted SQL, each check’s result, attempts, cost) plus a summary page	A reviewer understands one object in under a minute
12	Lineage and ordering: parse dependencies between views and objects, convert in order, score complexity	Dependent objects convert in the right sequence

Gate 2 (end of week 12): the LLM and KB steps show a measurable lift. If a local model gives no lift, switch repair to a hosted model and use local only for development. If even hosted gives none, the verification layer alone is still your product: report that and focus on it.

Phase 3: Harden (weeks 13-18)
Week	Work	Done when
13-14	Simple PL/SQL → PL/pgSQL (functions, then basic procedures). Unsupported constructs are flagged explicitly, not guessed	Defined supported subset documented
15	Workflow: CLI (parity convert ./sql), one git branch per object, PR output with the evidence report attached. Failed objects are never merged	End-to-end run produces reviewable PRs
16	Security: read-only DB accounts, secret/PII redaction before any model call, containers with --network none for generated code, no read-write bind mount to real files, audit log of every model call	Security checklist (below) all ticked
17	Test suite for Parity itself: unit tests for each verifier, golden-file tests for conversions, a pinned benchmark in CI	CI fails if the pass rate drops
18	Buffer week: fix bugs, tidy docs, handle slippage	Clean-machine install works

Gate 3: a friend runs docker compose up plus one command on a fresh machine and gets your published numbers (within noise).

Phase 4: Benchmark and showcase (weeks 19-22)
Week 19: Full benchmark on 500+ objects with the final model. Record pass rate, human-review rate, cost per object, time per object, and failures by category.
Week 20: README (one-line pitch, demo GIF, results table, architecture diagram, quickstart, limitations), 2-3 minute demo video, GitHub Pages site with sample reports.
Week 21: Blog post 1, “10 ways Oracle SQL silently changes meaning on Postgres.” Post 2, “Verification-first migration.”
Week 22: Share on LinkedIn, r/dataengineering, dbt and Postgres communities. File upstream sqlglot issues or fixes for the dialect bugs you found.
Phase 5: Launch and grow (weeks 23-36)
Pilot outreach: contact 10 consultancies or data teams with a short message: what you built, one concrete finding, an offer to convert 200-500 objects for free or at a low fixed price with success criteria agreed in advance.
Pilot proposal contents: scope, objects and dialects, success metric (for example verified pass rate and human-edit rate), data handling terms, timeline, price.
Second step based on demand: Teradata → Snowflake, deeper procedure support, or an on-prem packaging option, whichever pilots actually ask for.
Publication: release the benchmark dataset and taxonomy, and submit to a workshop or post on arXiv.
Only after a paying or committed pilot: SSO, role-based access, tamper-evident audit logs, hosted service.
Weekly routine (20 hrs)
Mon-Thu, 3 hrs/day: build.
Fri, 2 hrs: re-run the benchmark, log results, write down what failed.
Sat, 4 hrs: deeper work or learning (PL/SQL, Postgres internals, LangGraph).
Sun: off, plus a 15-minute plan for the next week.
Technical rules to follow throughout
Python, not TypeScript. sqlglot, sqlfluff, dbt, and database drivers are Python.
Deterministic first, LLM for the residue only.
The verifier decides, not the model. The LLM proposes, the checks accept or reject.
Never send raw rows to a model. Send counts, aggregates, hash-bucket mismatches, and column names.
Hard caps on attempts, tokens, and cost per object and per run.
Fix known bugs from agent.md before reusing any of it: duplicated tool execution, unsafe shell escaping (use docker cp or stdin instead of echo "$code"), checkpoints that rewind chat but not files, outdated model ID, zod .description() should be .describe(), and workspaceFolders.uri needing [0].
Security and legal checklist
Read-only database credentials for comparisons
Redaction pass before any model call
Sandboxed containers with no network for generated code
Audit log of every model call and tool run
Oracle free editions for development only; check terms before commercial use
Dataset licenses recorded; no private or customer SQL in public material
Trademark and name search done
Budget (cash, estimates)
Item	Estimate
LLM during development (mostly local/free tiers)	₹5,000 - ₹25,000
Final benchmark on a hosted model	₹5,000 - ₹40,000
Domain and misc.	₹1,000 - ₹5,000
Everything else (Docker, Postgres, GitHub, sqlglot, Pages)	₹0
Total	about ₹11,000 - ₹70,000
Metrics to track weekly

Corpus size, sqlglot-only pass rate, full pass rate, human-review rate, KB entries with tests, cost per object, average time per object, and test coverage. Publish them as they stand, and don’t set a target pass rate until the week 3 baseline exists.

Risk register and contingencies
Risk	Response
Falling behind	Use the week 18 buffer. Drop PL/SQL procedures first, then lineage, and keep verification and the KB
Local model too weak	Switch repair to a hosted model; keep local for development
A competitor ships similar verification	Lean on the open benchmark, the KB, and one pair done deeply
Corpus too easy or too narrow	Add harder objects and report results by complexity tier
Oracle container problems on your hardware (it needs a few GB of RAM)	Use Oracle XE or MySQL as the source, or start from SQL Server
Overclaiming	Say “verified on tested data” and list the checks
Burnout	Keep the Sunday off and the Friday review
Definition of done for the MVP
docker compose up plus one command reproduces your published numbers on a clean machine.
500+ objects benchmarked, with failures categorized.
20+ documented semantic differences, each with a test.
Per-object evidence reports and PR output working.
README, demo video, and two blog posts live.
Your first 7 days
Day 1: Name check, repo creation, license, project board.
Day 2: Install Docker and get Oracle Free and Postgres running.
Day 3: Load HR schema and run 10 queries you suspect differ on Postgres.
Day 4: Message 5 data engineers or consultants for short chats.
Day 5: Install sqlglot and transpile those 10 queries; run both versions and note which results differ.
Day 6: Write those differences into your first KB entries.
Day 7: Review, and set your weekly hours realistically.