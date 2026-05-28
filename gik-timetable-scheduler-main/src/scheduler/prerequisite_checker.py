"""
prerequisite_checker.py
Checks for prerequisite violations in a generated timetable.
"""

from collections import defaultdict
from src.models.student import Student

class PrerequisiteChecker:
    def __init__(self, courses, students, registrations):
        self.courses = {c.unique_id: c for c in courses}
        self.students = {s.student_id: s for s in students}
        self.registrations = registrations
        self.student_courses = self._build_student_course_map()

    def _build_student_course_map(self):
        student_courses = defaultdict(list)
        for reg in self.registrations:
            student_courses[reg.student_id].append(reg.course_unique_id)
        return student_courses

    def check(self):
        """
        Checks for concurrent-enrollment violations: a student is registered
        for a course AND one of its prerequisites in the SAME semester.

        Prerequisites are assumed to have been completed in prior semesters
        (we have no historical record). The only detectable violation is
        taking both the advanced course and its prerequisite concurrently.
        This correctly handles repeating students — they won't be flagged
        because their prerequisites appear in previous semesters, not now.

        Returns
        -------
        A list of violation message strings.
        """
        violations = []
        for student_id, course_ids in self.student_courses.items():
            # Build a set of bare course codes the student is taking this semester
            current_codes = set()
            for cid in course_ids:
                # course_unique_id is "CODE_SECTION" — extract just the code
                current_codes.add(cid.split("_")[0])

            for course_id in course_ids:
                course = self.courses.get(course_id)
                if not course or not course.prerequisites:
                    continue

                for prereq_code in course.prerequisites:
                    if not prereq_code:
                        continue
                    # Flag only if student is taking BOTH the advanced course
                    # AND its prerequisite this semester (concurrent enrollment)
                    if prereq_code in current_codes:
                        student = self.students.get(student_id)
                        student_name = student.name if student else "Unknown"
                        violations.append(
                            f"Student {student_name} ({student_id}) is taking "
                            f"'{course.title}' concurrently with its prerequisite '{prereq_code}'."
                        )
        return violations
