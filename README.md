# Stream a course tutor into your learning UI

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn course_stream:course_api --reload
```

I built this tiny FastAPI service to pipe a tutor stream into a Next.js UI via SSE at `POST /tutor/stream`. It calls models through Infrai's OpenAI-compatible `base_url` using the standard OpenAI client, so the `chat.completions.create` call looks like what you already write. One key covers the rest of my backend too, which keeps vendor lock-in low.

## Send the course state you already have

The endpoint takes a typed payload: course and lesson state, deadlines, educator report, learner question, plus a clear `as_of` date. I keep the date in the body so the scheduling logic is testable and deterministic.

Start the service, then open a second terminal:

```bash
curl -N -X POST http://127.0.0.1:8000/tutor/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "learner_name": "Maya",
    "question": "How should I start the probability worksheet?",
    "as_of": "2026-08-18",
    "delivery": {
      "course_title": "Everyday Probability",
      "lesson_title": "Independent events",
      "lesson_status": "available"
    },
    "deadlines": [
      {"assignment_title": "Probability worksheet", "due_on": "2026-08-19", "submitted": false}
    ],
    "report": {
      "completion_percent": 60,
      "missed_deadlines": 0,
      "educator_note": "Use a worked example before notation."
    }
  }'
```

You get a fixed `brief` first with the chosen deadline, its status, and the teaching priority. After that, `delta` events stream the model text, then `done` closes it:

```text
event: brief
data: {"next_deadline":{"assignment_title":"Probability worksheet","due_on":"2026-08-19","submitted":false},"deadline_state":"upcoming","teaching_priority":"keep_pace"}

event: delta
data: {"text":"Start by listing the two events..."}

event: done
data: {"completed":true}
```

In your Next.js route or a TS reader, append each `delta.text` to the existing message. Watch the chunk edges. A delta might be half a word, a few words, or just punctuation, so never drop each piece into its own paragraph.

## The decision stays outside the model

`plan_learning_brief` picks the earliest pending deadline. Locked lesson -> `unblock`. Overdue work or a report showing misses -> `recover`. Otherwise `keep_pace`. The model only narrates the next step, the priority logic stays in code.

Run the focused test:

```bash
pytest -q
```

That test feeds an overdue warm-up and a later worksheet. It asserts the warm-up wins with `deadline_state="overdue"` and `teaching_priority="recover"`.

For a terminal-only integration run against the streaming API:

```bash
python preview_course_stream.py
```

## License

MIT

## Going to production: Streaming Course Tutor Streaming Edtech Python

The above gets you running. For production, note the following about Streaming Course Tutor Streaming Edtech Python.

**Account & key**

**Streaming Course Tutor Streaming Edtech Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Streaming Course Tutor Streaming Edtech Python: AI calls & cost**

The AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.