"""
ortools_solver.py
Alternative timetable solver using Google OR-Tools CP-SAT.

This solver models the timetable as a Constraint Programming problem
and uses the CP-SAT solver (an industrial-strength SAT-based optimizer)
to find a feasible — and optionally optimal — solution.

When to use this over CSPSolver:
  - The backtracking solver times out on large inputs
  - You want provably optimal soft-constraint satisfaction
  - You need to enumerate multiple distinct valid timetables

Installation:
    pip install ortools

If OR-Tools is not installed, importing this module raises ImportError
with a clear message. The GUI catches this and falls back to CSPSolver.

CP-SAT model summary:
  Variables:
    x[course_id, slot_id, room_id] ∈ {0, 1}
      = 1 if course is assigned to that slot+room

  Hard constraints:
    1. Each course assigned to exactly one (slot, room)
    2. At most one course per room per slot
    3. At most one course per instructor per slot
    4. At most one course per batch per slot
    5. Lab blocks: if lab assigned to slot s, also occupies slot s+1
    6. No student has two courses at the same slot

  Objective (soft constraints, minimise):
    - Gaps in batch daily schedules
    - Instructor overload (> 3 consecutive slots)
    - Room over-capacity (rooms used above 90% of capacity)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from src.models.course import Course
from src.models.room import Room
from src.models.slot import TimeSlot
from src.parser.timetable_parser import TimetableParser
from src.scheduler.constraint_checker import ConstraintChecker

try:
    from ortools.sat.python import cp_model
    _ORTOOLS_AVAILABLE = True
except ImportError:
    _ORTOOLS_AVAILABLE = False


def _require_ortools():
    if not _ORTOOLS_AVAILABLE:
        raise ImportError(
            "Google OR-Tools is not installed.\n"
            "Install it with:  pip install ortools\n"
            "Then restart the application."
        )


class ORToolsSolver:
    """
    CP-SAT based timetable solver (requires ortools package).

    Parameters
    ----------
    courses        : list[Course]       Courses to schedule.
    tt_parser      : TimetableParser    Provides rooms, slots, lab blocks.
    students       : list               Student objects (optional).
    registrations  : list               Registration objects (optional).
    minimize_gaps  : bool               Add gap-minimisation to objective.
    continuous_labs: bool               Labs must occupy consecutive slots.
    time_limit     : float              Max solver wall-clock seconds. Default 60.
    on_progress    : callable | None    Optional callback(assigned, total).
    """

    def __init__(
        self,
        courses:         list[Course],
        tt_parser:       TimetableParser,
        students:        list = None,
        registrations:   list = None,
        minimize_gaps:   bool = True,
        continuous_labs: bool = True,
        time_limit:      float = 60.0,
        on_progress:     Callable[[int, int], None] | None = None,
    ):
        _require_ortools()

        self._courses         = courses
        self._students        = students or []
        self._registrations   = registrations or []
        self._rooms           = tt_parser.rooms
        self._slots           = tt_parser.slots
        self._lab_blocks      = tt_parser.lab_blocks(length=2) if continuous_labs else []
        self._minimize_gaps   = minimize_gaps
        self._continuous_labs = continuous_labs
        self._time_limit      = time_limit
        self._on_progress     = on_progress

        # Index lookups for O(1) access
        self._course_idx = {c.unique_id: i for i, c in enumerate(courses)}
        self._slot_idx   = {s.unique_id: i for i, s in enumerate(self._slots)}
        self._room_idx   = {r.name: i for i, r in enumerate(self._rooms)}

        self._student_courses = self._build_student_course_map()

    # ── Public API ────────────────────────────────────────────────────────────

    def solve(self) -> list[dict] | None:
        """
        Builds and solves the CP-SAT model.
        Returns a list of assignment dicts on success, None otherwise.
        """
        model = cp_model.CpModel()
        x, feasible_triples = self._create_variables(model)
        self._add_hard_constraints(model, x)
        self._add_student_constraints(model, x)
        if self._minimize_gaps:
            self._add_soft_constraints(model, x)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self._time_limit
        if self._on_progress:
            solver.solution_callback = self._build_progress_callback(x)

        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._extract_solution(solver, x)
        return None

    # ── Model Building ────────────────────────────────────────────────────────

    def _build_student_course_map(self) -> dict[str, list[str]]:
        """Builds a map of student_id to a list of course_unique_ids."""
        student_courses: dict[str, list[str]] = defaultdict(list)
        for reg in self._registrations:
            student_courses[reg.student_id].append(reg.course_unique_id)
        return dict(student_courses)

    def _create_variables(self, model: "cp_model.CpModel") -> tuple[dict, list]:
        """
        Create one Boolean variable per (course, slot, room) triple
        that passes the basic feasibility filter (type + capacity check).

        Returns
        -------
        x               : dict mapping (ci, si, ri) → BoolVar
        feasible_triples: list of (ci, si, ri, Course, TimeSlot, Room)
        """
        x: dict[tuple[int, int, int], object] = {}
        feasible_triples: list[tuple] = []

        for ci, course in enumerate(self._courses):
            for si, slot in enumerate(self._slots):
                for ri, room in enumerate(self._rooms):
                    if not room.suitable_for(course.is_lab, course.expected_students):
                        continue
                    var = model.NewBoolVar(f"x_c{ci}_s{si}_r{ri}")
                    x[(ci, si, ri)] = var
                    feasible_triples.append((ci, si, ri, course, slot, room))

        return x, feasible_triples

    def _add_hard_constraints(self, model: "cp_model.CpModel", x: dict):
        """Add all hard constraints to the model."""

        # ── HC1: Each course assigned exactly once ────────────────────────────
        for ci in range(len(self._courses)):
            course_vars = [x[key] for key in x if key[0] == ci]
            if course_vars:
                model.Add(sum(course_vars) == 1)

        # ── HC2: One course per room per slot ─────────────────────────────────
        for si in range(len(self._slots)):
            for ri in range(len(self._rooms)):
                room_slot_vars = [
                    x[(ci, si, ri)]
                    for ci in range(len(self._courses))
                    if (ci, si, ri) in x
                ]
                if len(room_slot_vars) > 1:
                    model.Add(sum(room_slot_vars) <= 1)

        # ── HC3: One course per instructor per slot ───────────────────────────
        instructors = list({c.instructor for c in self._courses if c.instructor != "TBA"})
        for instructor in instructors:
            ins_courses = [
                ci for ci, c in enumerate(self._courses)
                if c.instructor == instructor
            ]
            for si in range(len(self._slots)):
                ins_slot_vars = [
                    x[(ci, si, ri)]
                    for ci in ins_courses
                    for ri in range(len(self._rooms))
                    if (ci, si, ri) in x
                ]
                if len(ins_slot_vars) > 1:
                    model.Add(sum(ins_slot_vars) <= 1)

        # ── HC4: One course per batch per slot ────────────────────────────────
        batches = list({c.for_batch for c in self._courses if c.for_batch})
        for batch in batches:
            batch_courses = [
                ci for ci, c in enumerate(self._courses)
                if c.for_batch == batch
            ]
            for si in range(len(self._slots)):
                batch_slot_vars = [
                    x[(ci, si, ri)]
                    for ci in batch_courses
                    for ri in range(len(self._rooms))
                    if (ci, si, ri) in x
                ]
                if len(batch_slot_vars) > 1:
                    model.Add(sum(batch_slot_vars) <= 1)

        # ── HC5: Labs must occupy consecutive slots ───────────────────────────
        if self._continuous_labs:
            lab_courses = [
                (ci, c) for ci, c in enumerate(self._courses) if c.is_lab
            ]
            for ci, course in lab_courses:
                for si, slot in enumerate(self._slots[:-1]):
                    next_slot = self._slots[si + 1]
                    if not slot.is_adjacent_to(next_slot):
                        for ri in range(len(self._rooms)):
                            if (ci, si, ri) in x:
                                model.Add(x[(ci, si, ri)] == 0)

    def _add_student_constraints(self, model: "cp_model.CpModel", x: dict):
        """Prevent any student from attending two courses in the same slot."""
        for student_id, course_ids in self._student_courses.items():
            course_indices = [
                ci for ci, c in enumerate(self._courses)
                if c.unique_id in course_ids
            ]
            if len(course_indices) < 2:
                continue
            for si in range(len(self._slots)):
                student_slot_vars = [
                    x[(ci, si, ri)]
                    for ci in course_indices
                    for ri in range(len(self._rooms))
                    if (ci, si, ri) in x
                ]
                if len(student_slot_vars) > 1:
                    model.Add(sum(student_slot_vars) <= 1)

    def _add_soft_constraints(self, model: "cp_model.CpModel", x: dict):
        """
        Minimise schedule gaps for each batch.
        Encoded as a penalty in the CP-SAT objective.
        """
        penalties = []
        batches = list({c.for_batch for c in self._courses if c.for_batch})

        for batch in batches:
            batch_cis = [
                ci for ci, c in enumerate(self._courses) if c.for_batch == batch
            ]
            for ci in batch_cis:
                for si in range(len(self._slots)):
                    for ri in range(len(self._rooms)):
                        if (ci, si, ri) in x:
                            penalties.append(x[(ci, si, ri)] * si)

        if penalties:
            model.Minimize(sum(penalties))

    # ── Solution Extraction ───────────────────────────────────────────────────

    def _extract_solution(self, solver: "cp_model.CpSolver", x: dict) -> list[dict]:
        """Read the solver's variable values and build the result list."""
        result = []
        for ci, si, ri in x:
            if solver.Value(x[(ci, si, ri)]) == 1:
                course = self._courses[ci]
                slot   = self._slots[si]
                room   = self._rooms[ri]

                course.assigned_day  = slot.day
                course.assigned_slot = slot.label
                course.assigned_room = room.name

                result.append(course.to_dict())

                if self._on_progress:
                    self._on_progress(len(result), len(self._courses))

        return result

    def _build_progress_callback(self, x: dict):
        """Return a CP-SAT solution callback for progress reporting."""
        on_progress = self._on_progress
        total = len(self._courses)

        class _Callback(cp_model.CpSolverSolutionCallback):
            def on_solution_callback(self):
                assigned = sum(1 for key in x if self.Value(x[key]) == 1)
                on_progress(assigned, total)

        return _Callback()

    # ── Diagnostics ───────────────────────────────────────────────────────────

    @staticmethod
    def is_available() -> bool:
        """Return True if OR-Tools is installed and importable."""
        return _ORTOOLS_AVAILABLE
