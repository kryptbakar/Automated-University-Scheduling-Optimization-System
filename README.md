# Automated-University-Scheduling-Optimization-System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)  

---

## 🚀 Project Overview
This project provides an automated semester scheduling solution built for the GIK Institute's Spring 2026 catalogue. It generates weekly timetables (Mon–Fri) using a Constraint Satisfaction Problem (CSP) greedy solver, supporting room/slot constraints, avoiding conflicts, and exporting Excel files with official-like layouts. The system can greatly reduce the administrative burden of building error-free, conflict-free academic schedules for universities.

---

## 🧾 Recruiter-Friendly Summary
- Builds a recurring weekly timetable (Mon–Fri) from structured course inputs.
- Enforces hard constraints (no clashes) while optimizing soft objectives.
- Provides both a GUI workflow and a CLI batch workflow.
- Outputs an Excel timetable that mirrors the official institutional layout.

---

## ✨ Key Technical Features
- Greedy CSP scheduling with rule-based constraint checking
- Teacher/room/section conflict prevention
- Room locking for multi-session courses
- PDF-style slot rules (including Friday shift) reflected in output
- CustomTkinter GUI for non-technical users
- Excel exporter designed to match official timetable formatting

---

## 🛠️ Tech Stack & Dependencies
- Python 3.10+
- CustomTkinter (GUI)
- pandas (data handling)
- openpyxl / xlsxwriter (Excel output)

---

## 📁 Project Structure (High Level)
```
Automated-University-Scheduling-Optimization-System/
├── config.py                     # building / room / lab / break configuration
├── main.py                       # entry point (GUI default, --cli for headless)
├── src/
│   ├── parser/                   # courses.xlsx + institutional timetable readers
│   ├── scheduler/                # CSP solver, constraint checker, room allocator
│   ├── exporter/                 # Excel writer (PDF-style grid)
│   └── models/                   # Course / Room / TimeSlot dataclasses
├── gui/
│   ├── main_window.py            # root shell, sidebar, top bar
│   ├── upload_panel.py           # one-click generate flow
│   ├── timetable_view.py         # semester grid render (recurring weekly view)
│   └── stats_view.py             # per-day / per-building statistics
├── data/                         # input course list + GIK reference PDF
├── output/                       # generated timetables
└── report/                       # IEEE project report (.docx)
```

---

## 📥 Inputs / 📤 Outputs
### Input
- `data/courses.xlsx`
  - Typical columns: Code, Sec, Course Title, CHs, Course Instructor, For, Exp Nos.

### Output
- `output/timetable.xlsx`
  - Room × slot grid grouped by building
  - Friday rendered with shifted morning grid (10:00 / 11:00 / 12:00)
  - Cells color-coded by department (if enabled)

---

## ✅ Constraints
### Hard Constraints (Always Enforced)
- No teacher double-booked.
- No room double-booked.
- No section taught twice on the same day.
- All sessions of a course share one locked room.

### Soft Objectives (Optimized When Possible)
- Day-load balancing (least-loaded day first; Friday seeded heavier so it stays light).
- Penalty for stacking 3 consecutive slots on one instructor in one day.
- Capacity-aware room allocation with wider-room fallback.
- Last-resort lab fallback to virtual/TBA copies.

---

## ▶️ Quick Start
```bash
pip install -r requirements.txt

# GUI
python main.py

# CLI
python main.py --cli --courses data/courses.xlsx --output output/timetable.xlsx
```

---

## 🧩 How It Works (Scheduling Pipeline)
1. Load and normalize courses from the Excel file.
2. Build a slot/room universe from `config.py` (buildings, labs, breaks, allowed slots).
3. Use the scheduler to assign each required session into feasible (day, time, room) tuples.
4. Validate assignments with constraint checker.
5. Emit an Excel grid formatted to match the institutional timetable layout.

---

## 📌 Tips
- Keep instructor names consistent across rows to avoid duplicate identity collisions.
- If a course requires multiple weekly sessions, ensure it is represented correctly in the input.
- If constraints are too strict for available capacity, consider adding more rooms/slots in `config.py`.

---

## 👥 Group
- Ismail Waqar — 2023453
- Abubakar — 2023352
- Usman — 2023581
- Ali Muntazir — 2023098

CS378 - Design and Analysis of Algorithms - Spring 2026

---

## 🤝 Contributing
This is an academic project. Suggestions and improvements are welcome via issues/PRs.

---

## 📄 License
If a LICENSE file exists in the repository, it applies. Otherwise, treat as “All Rights Reserved” by default.

---

## Appendix: Original README (Preserved)

# GIK Timetable Scheduler

Automated semester timetable generator for GIK Institute, built for the
Spring 2026 catalogue. The semester schedule is published as a recurring
weekly grid (Mon–Fri) that every teaching week of the semester follows.
Implemented as a greedy CSP solver with PDF-aware room/slot rules, a
CustomTkinter GUI, and an Excel exporter that mirrors the official
timetable layout.

## Quick start

```bash
pip install -r requirements.txt

# GUI
python main.py

# CLI
python main.py --cli --courses data/courses.xlsx --output output/timetable.xlsx
```

## Inputs / Outputs

- **Input**: `data/courses.xlsx` — Code, Sec, Course Title, CHs, Course Instructor, For, Exp Nos.
- **Output**: `output/timetable.xlsx` — room x slot grid grouped by building,
  Friday rendered with its shifted morning grid (10:00 / 11:00 / 12:00),
  cells colour-coded by department.

## Project layout

```
config.py                     # building / room / lab / break configuration
main.py                       # entry point (GUI default, --cli for headless)
src/
  parser/                     # courses.xlsx + institutional timetable readers
  scheduler/                  # CSP solver, constraint checker, room allocator
  exporter/                   # Excel writer (PDF-style grid)
  models/                     # Course / Room / TimeSlot dataclasses
gui/
  main_window.py              # root shell, sidebar, top bar
  upload_panel.py             # one-click generate flow
  timetable_view.py           # semester grid render (recurring weekly view)
  stats_view.py               # per-day / per-building statistics
data/                         # input course list + GIK reference PDF
report/                       # IEEE project report (.docx)
```

## Constraints

Hard rules are enforced via O(1) hash-map lookups in
`src/scheduler/constraint_checker.py`:

- No teacher double-booked.
- No room double-booked.
- No section taught twice on the same day.
- All sessions of a course share one locked room.

Soft objectives in `csp_solver.py` and `constraint_checker.py`:

- Day-load balancing (least-loaded day first; Friday seeded heavier so it
  stays light, matching the PDF).
- Penalty for stacking 3 consecutive slots on one instructor in one day.
- Capacity-aware room allocation with a wider-room fallback.
- Last-resort lab fallback to virtual TBA copies.

## Group

- Ismail Waqar — 2023453
- Abubakar — 2023352
- Usman — 2023581
- Ali Muntazir — 2023098

CS378 - Design and Analysis of Algorithms - Spring 2026
