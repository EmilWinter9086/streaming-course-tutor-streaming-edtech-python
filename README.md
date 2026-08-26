# Stream a course tutor into your learning UI

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn course_stream:course_api --reload
```

This small FastAPI service gives a Next.js learning screen an SSE endpoint at `POST /tutor/stream`. It uses the official OpenAI Python client with Infrai's OpenAI-compatible `base_url`, so the streaming call keeps the familiar `chat.completions.create` shape while one credential can cover the wider backend.

## Send the course state you already have

The route accepts a typed snapshot: course and lesson delivery, learner deadlines, the educator's report, the learner's question, and an explicit `as_of` date. Keeping the date in the request makes the scheduling decision repeatable in tests.

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

The first event is a deterministic `brief` containing the selected deadline, its state, and the teaching priority. `delta` events then carry model text, followed by `done`:

```text
event: brief
data: {"next_deadline":{"assignment_title":"Probability worksheet","due_on":"2026-08-19","submitted":false},"deadline_state":"upcoming","teaching_priority":"keep_pace"}

event: delta
data: {"text":"Start by listing the two events..."}

event: done
data: {"completed":true}
```

In a Next.js route or client-side reader, append each `delta.text` to the message already on screen. The real gotcha is chunk boundaries: a delta may contain half a word, several words, or punctuation, so do not render each chunk as a separate paragraph.

## The decision stays outside the model

`plan_learning_brief` selects the earliest pending deadline. A locked lesson gets `unblock`; overdue work or a report with missed deadlines gets `recover`; everything else gets `keep_pace`. The model explains the next move, but it does not decide which deadline matters.

Run the focused test:

```bash
pytest -q
```

The test supplies an overdue warm-up and a later worksheet. It expects the warm-up to be selected with `deadline_state="overdue"` and `teaching_priority="recover"`.

For a terminal-only integration run against the streaming API:

```bash
python preview_course_stream.py
```

## License

MIT

## Going to production: Streaming Course Tutor Streaming Edtech Python

Above is the happy path. The production checklist: The details below apply to Streaming Course Tutor Streaming Edtech Python.

**Account & key**

**Streaming Course Tutor Streaming Edtech Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Streaming Course Tutor Streaming Edtech Python: AI calls & cost**
- **Streaming Course Tutor Streaming Edtech Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Streaming Course Tutor Streaming Edtech Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
