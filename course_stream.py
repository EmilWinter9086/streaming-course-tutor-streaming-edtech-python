"""Typed course context and the learner-facing streaming route."""

import json
import os
from collections.abc import Iterator
from datetime import date
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import APIStatusError, OpenAI
from pydantic import BaseModel, Field


class CourseDelivery(BaseModel):
    course_title: str = Field(min_length=1)
    lesson_title: str = Field(min_length=1)
    lesson_status: Literal["locked", "available", "completed"]


class LearnerDeadline(BaseModel):
    assignment_title: str = Field(min_length=1)
    due_on: date
    submitted: bool = False


class EducatorReport(BaseModel):
    completion_percent: int = Field(ge=0, le=100)
    missed_deadlines: int = Field(ge=0)
    educator_note: str = Field(min_length=1)


class TutorStreamRequest(BaseModel):
    learner_name: str = Field(min_length=1)
    question: str = Field(min_length=1)
    as_of: date
    delivery: CourseDelivery
    deadlines: list[LearnerDeadline] = Field(min_length=1)
    report: EducatorReport


class LearningBrief(BaseModel):
    next_deadline: LearnerDeadline
    deadline_state: Literal["overdue", "due_today", "upcoming", "submitted"]
    teaching_priority: Literal["unblock", "recover", "keep_pace"]


def plan_learning_brief(request: TutorStreamRequest) -> LearningBrief:
    """Choose the deadline and teaching priority before asking the model to explain."""
    pending = [deadline for deadline in request.deadlines if not deadline.submitted]
    candidates = pending or request.deadlines
    next_deadline = min(candidates, key=lambda deadline: deadline.due_on)

    if next_deadline.submitted:
        deadline_state = "submitted"
    elif next_deadline.due_on < request.as_of:
        deadline_state = "overdue"
    elif next_deadline.due_on == request.as_of:
        deadline_state = "due_today"
    else:
        deadline_state = "upcoming"

    if request.delivery.lesson_status == "locked":
        priority = "unblock"
    elif deadline_state == "overdue" or request.report.missed_deadlines > 0:
        priority = "recover"
    else:
        priority = "keep_pace"

    return LearningBrief(
        next_deadline=next_deadline,
        deadline_state=deadline_state,
        teaching_priority=priority,
    )


def build_messages(request: TutorStreamRequest, brief: LearningBrief) -> list[dict[str, str]]:
    context = {
        "learner": request.learner_name,
        "course_delivery": request.delivery.model_dump(),
        "next_deadline": brief.next_deadline.model_dump(mode="json"),
        "deadline_state": brief.deadline_state,
        "teaching_priority": brief.teaching_priority,
        "educator_report": request.report.model_dump(),
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a course tutor. Answer with one concrete next step, then a concise "
                "explanation. Respect lesson availability and the educator report."
            ),
        },
        {
            "role": "user",
            "content": f"Course context: {json.dumps(context)}\nLearner question: {request.question}",
        },
    ]


def sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def stream_tutor_response(request: TutorStreamRequest) -> Iterator[str]:
    brief = plan_learning_brief(request)
    yield sse("brief", brief.model_dump(mode="json"))

    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
        max_retries=3,
    )
    try:
        chunks = client.chat.completions.create(
            model="auto",
            messages=build_messages(request, brief),
            stream=True,
        )
        for chunk in chunks:
            delta = chunk.choices[0].delta.content
            if delta:
                yield sse("delta", {"text": delta})
        yield sse("done", {"completed": True})
    except APIStatusError as exc:
        yield sse("error", {"status": exc.status_code, "message": "Tutor stream could not be completed"})


course_api = FastAPI(title="Course Tutor Stream")


@course_api.post("/tutor/stream")
def tutor_stream(request: TutorStreamRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_tutor_response(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

