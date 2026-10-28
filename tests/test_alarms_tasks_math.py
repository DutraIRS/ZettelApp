from datetime import UTC, datetime, timedelta

from zettelapp.core.render import NoteRenderer
from zettelapp.core.textutil import MATH_RE, find_tasks, strip_markdown, toggle_task


def _iso(delta_minutes):
    return (datetime.now(UTC) + timedelta(minutes=delta_minutes)).isoformat(timespec="seconds")


def test_alarm_is_due_once_and_resets_when_changed(vault):
    n = vault.create_note("Call the bank")
    n.alarm = _iso(-1)
    vault.save_note(n)
    assert [x.id for x in vault.due_alarms()] == [n.id]
    vault.mark_alarm_fired(n.id)
    assert vault.due_alarms() == []
    assert vault.pending_alarm_count() == 0
    # Saving without changing the alarm doesn't re-arm it...
    n = vault.get_note(n.id)
    n.body = "edited"
    vault.save_note(n)
    assert vault.due_alarms() == []
    # ...but moving it does.
    n.alarm = _iso(-2)
    vault.save_note(n)
    assert [x.id for x in vault.due_alarms()] == [n.id]


def test_future_trashed_and_invalid_alarms_do_not_fire(vault):
    future = vault.create_note("later")
    future.alarm = _iso(60)
    vault.save_note(future)
    gone = vault.create_note("gone")
    gone.alarm = _iso(-5)
    vault.save_note(gone)
    vault.trash_note(gone.id)
    bad = vault.create_note("bad")
    bad.alarm = "tomorrow-ish"
    vault.save_note(bad)
    assert vault.get_note(bad.id).alarm == ""
    assert vault.due_alarms() == []
    assert vault.pending_alarm_count() == 1


def test_naive_alarm_is_read_as_local_time(vault):
    n = vault.create_note("x")
    local = datetime.now().replace(microsecond=0) + timedelta(hours=2)
    n.alarm = local.isoformat()
    vault.save_note(n)
    saved = datetime.fromisoformat(vault.get_note(n.id).alarm)
    assert saved.tzinfo is not None
    assert abs((saved - datetime.now(UTC)).total_seconds() - 7200) < 5


def test_find_and_toggle_tasks():
    text = "- [ ] one\n- [x] two\n```\n- [ ] code\n```\nnot [ ] a task"
    assert [t[2] for t in find_tasks(text)] == [False, True]
    assert toggle_task(text, 0).startswith("- [x] one")
    assert toggle_task(text, 1).splitlines()[1] == "- [ ] two"
    assert toggle_task(text, 5) == text
    assert "[ ]" not in strip_markdown("- [ ] buy milk")


def test_renderer_checklists_are_links_only_in_the_preview():
    body = "- [ ] a\n- [x] b"
    live = NoteRenderer(lambda t: None, task_links=True).render(body)
    assert 'href="zettel-task:0"' in live and 'href="zettel-task:1"' in live
    plain = NoteRenderer(lambda t: None).render(body)
    assert "zettel-task" not in plain and "\u2610" in plain and "\u2611" in plain


def test_math_detection_ignores_prices_and_code():
    assert MATH_RE.search("It costs $5 and $10 total") is None
    html = NoteRenderer(lambda t: None, math_href=lambda latex, d: "math:" + latex).render(
        "Euler $e^{i\\pi}+1=0$\n\n$$\\frac{a}{b}$$\n\n`$x$`"
    )
    assert html.count("<img") == 2
    assert "<code>$x$</code>" in html


def test_math_without_image_support_stays_text():
    html = NoteRenderer(lambda t: None).render("$a_b$")
    assert "<img" not in html and "$a_b$" in html


def test_an_alarm_edited_into_the_database_by_hand_never_breaks_the_check(vault):
    odd = vault.create_note("odd")
    local = vault.create_note("local")
    with vault.transaction():
        vault.conn.execute("UPDATE notes SET alarm = 'not a time' WHERE id = ?", (odd.id,))
        vault.conn.execute(
            "UPDATE notes SET alarm = ? WHERE id = ?",
            ((datetime.now() - timedelta(minutes=5)).isoformat(), local.id),  # naive, local
        )
    assert [n.id for n in vault.due_alarms()] == [local.id]
