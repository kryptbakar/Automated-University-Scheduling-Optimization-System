"""
registration_parser.py
Reads the student registration Excel file and returns lists of Student and Registration objects.

Expected Excel columns for registrations (order-independent):
    StudentID       → student's unique ID
    CourseCode      → course code, e.g. "CS101"
    Section         → section identifier, e.g. "A"

Expected Excel columns for students (optional, in a separate sheet):
    StudentID       → student's unique ID
    StudentName     → full name of the student
    Batch           → student's batch/programme
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

from src.models.student import Student
from src.models.registration import Registration

def _clean_str(val) -> str:
    """Return a stripped string, or empty string for NaN/None."""
    if pd.isna(val):
        return ""
    return str(val).strip()

class RegistrationParser:
    """
    Parses an Excel file containing student registrations and student details.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._students: dict[str, Student] = {}
        self._registrations: list[Registration] = []
        self._errors: list[str] = []

    def parse(self) -> tuple[list[Student], list[Registration]]:
        """
        Parses the student and registration data from the Excel file.

        Returns
        -------
        A tuple containing:
            - A list of Student objects.
            - A list of Registration objects.
        """
        if not self.path.exists():
            # It's okay if the registration file doesn't exist.
            # Return empty lists in that case.
            return [], []

        try:
            # Try to read student details first
            self._parse_students(pd.read_excel(self.path, sheet_name="Students"))
        except Exception:
            # If 'Students' sheet doesn't exist or fails, ignore.
            pass

        try:
            self._parse_registrations(pd.read_excel(self.path, sheet_name="Registrations"))
        except Exception as e:
            self._errors.append(f"Could not parse registrations: {e}")

        return list(self._students.values()), self._registrations

    def _parse_students(self, df: pd.DataFrame):
        """Parses the students DataFrame."""
        for _, row in df.iterrows():
            student_id = _clean_str(row.get("StudentID"))
            if student_id:
                self._students[student_id] = Student(
                    student_id=student_id,
                    name=_clean_str(row.get("StudentName", "")),
                    batch=_clean_str(row.get("Batch", ""))
                )

    def _parse_registrations(self, df: pd.DataFrame):
        """Parses the registrations DataFrame."""
        for _, row in df.iterrows():
            student_id = _clean_str(row.get("StudentID"))
            course_code = _clean_str(row.get("CourseCode"))
            section = _clean_str(row.get("Section"))

            if student_id and course_code and section:
                self._registrations.append(
                    Registration(
                        student_id=student_id,
                        course_code=course_code,
                        section=section
                    )
                )
                # If a student is registered but not in the students list, add them.
                if student_id not in self._students:
                    self._students[student_id] = Student(student_id=student_id, name="Unknown", batch="Unknown")

    @property
    def errors(self) -> list[str]:
        return self._errors
