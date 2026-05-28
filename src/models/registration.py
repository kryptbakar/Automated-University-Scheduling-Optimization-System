"""
registration.py
Represents a single student registration for a course.
"""

from dataclasses import dataclass

@dataclass
class Registration:
    """
    Represents a student's registration in a course section.

    Attributes
    ----------
    student_id : str
        The ID of the student.
    course_code : str
        The code of the course.
    section : str
        The section of the course.
    """
    student_id: str
    course_code: str
    section: str

    @property
    def course_unique_id(self) -> str:
        """
        Returns the unique identifier for the course section.
        e.g., CS101_A
        """
        return f"{self.course_code}_{self.section}"
