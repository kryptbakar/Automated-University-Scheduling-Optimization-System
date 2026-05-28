"""
student.py
Represents a single student in the system.
"""

from dataclasses import dataclass

@dataclass
class Student:
    """
    Represents a student.

    Attributes
    ----------
    student_id : str
        Unique identifier for the student.
    name : str
        Full name of the student.
    batch : str
        The batch or programme the student belongs to.
    """
    student_id: str
    name: str
    batch: str
