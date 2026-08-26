from course_stream import TutorStreamRequest, plan_learning_brief


def test_overdue_work_switches_the_teaching_priority_to_recovery() -> None:
    request = TutorStreamRequest.model_validate(
        {
            "learner_name": "Maya",
            "question": "What should I work on next?",
            "as_of": "2026-08-18",
            "delivery": {
                "course_title": "Everyday Probability",
                "lesson_title": "Independent events",
                "lesson_status": "available",
            },
            "deadlines": [
                {"assignment_title": "Warm-up quiz", "due_on": "2026-08-17", "submitted": False},
                {"assignment_title": "Worksheet", "due_on": "2026-08-20", "submitted": False},
            ],
            "report": {
                "completion_percent": 45,
                "missed_deadlines": 1,
                "educator_note": "Review the first missed task.",
            },
        }
    )

    brief = plan_learning_brief(request)

    assert brief.next_deadline.assignment_title == "Warm-up quiz"
    assert brief.deadline_state == "overdue"
    assert brief.teaching_priority == "recover"

