"""Print one realistic SSE session without starting a browser client."""

from course_stream import TutorStreamRequest, stream_tutor_response


sample = TutorStreamRequest.model_validate(
    {
        "learner_name": "Maya",
        "question": "How should I start the probability worksheet?",
        "as_of": "2026-08-18",
        "delivery": {
            "course_title": "Everyday Probability",
            "lesson_title": "Independent events",
            "lesson_status": "available",
        },
        "deadlines": [
            {"assignment_title": "Probability worksheet", "due_on": "2026-08-19", "submitted": False},
            {"assignment_title": "Reflection", "due_on": "2026-08-22", "submitted": False},
        ],
        "report": {
            "completion_percent": 60,
            "missed_deadlines": 0,
            "educator_note": "Use a worked example before notation.",
        },
    }
)

for event in stream_tutor_response(sample):
    print(event, end="")

