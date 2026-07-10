from flask import Flask, redirect, url_for, render_template, request
import sqlite3, calendar
from datetime import date, datetime, timedelta

def insert_task(title, assignedTo, createdBy, details, due_date, duration):
    conn = sqlite3.connect("tasks.db")
    conn.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    assignedTo TEXT,
    createdBy TEXT,
    details TEXT,
    priority TEXT,
    status TEXT,
    due_date TEXT,
    duration INTEGER,
    scheduled_date TEXT,
    scheduled_start TEXT,
    scheduled_end TEXT,
    scheduled INTEGER DEFAULT 0
)
""")
    conn.execute("""
INSERT INTO tasks(
    title,
    assignedTo,
    createdBy,
    details,
    priority,
    status,
    due_date,
    duration
)
VALUES (?,?,?,?,?,?,?,?)
""",
(
    title,
    assignedTo,
    createdBy,
    details,
    "Medium",
    "Not started",
    due_date,
    duration
))
    conn.commit()
    conn.close()
    
def find_tasks_indiv(name):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.execute("SELECT * FROM tasks WHERE assignedTo = ? AND priority = ?", (name,"Low"))
    low = cursor.fetchall()
    cursor = conn.execute("SELECT * FROM tasks WHERE assignedTo = ? AND priority = ?", (name,"Medium"))
    medium = cursor.fetchall()
    cursor = conn.execute("SELECT * FROM tasks WHERE assignedTo = ? AND priority = ?", (name,"High"))
    high = cursor.fetchall()
    conn.close()
    return low, medium, high

def all_tasks():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.execute("SELECT * FROM tasks WHERE priority = ?", ("Low",))
    low = cursor.fetchall()
    cursor = conn.execute("SELECT * FROM tasks WHERE priority = ?", ("Medium",))
    medium = cursor.fetchall()
    cursor = conn.execute("SELECT * FROM tasks WHERE priority = ?", ("High",))
    high = cursor.fetchall()
    conn.close()
    return low, medium, high

def get_unscheduled_tasks():
    conn = sqlite3.connect("tasks.db")
    tasks = conn.execute("""
        SELECT
            id,
            title,
            duration,
            priority
        FROM tasks
        WHERE scheduled = 0
        ORDER BY priority DESC
    """).fetchall()

    conn.close()
    return tasks

def update_status(ID, status):
    conn = sqlite3.connect("tasks.db")
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, ID))
    conn.commit()
    conn.close()
    
def update_priority(ID, priority):
    conn = sqlite3.connect("tasks.db")
    conn.execute("UPDATE tasks SET priority = ? WHERE id = ?", (priority, ID))
    conn.commit()
    conn.close()

def create_event(title, date, start, end, details):
    conn = sqlite3.connect("tasks.db")
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, title, date, start, end, details)")
    conn.execute("INSERT INTO events(title, date, start, end, details) VALUES (?,?,?,?,?)", (title, date, start, end, details))
    conn.commit()
    conn.close()
    
def curr_week(offset):
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_start += timedelta(weeks=offset)
    week = []
    for i in range(7):
        week.append(week_start + timedelta(days=i))
    start = week[0]
    end = week[-1]
    title = f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
    return week, title

def curr_events(week_start):
    
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = (week_start + timedelta(days=6)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect("tasks.db")
    try:
        events = conn.execute("SELECT title, date, start, end, details, id FROM events WHERE date >= ? AND date <= ? ORDER BY date, start", (week_start_str, week_end_str)).fetchall()

        conn.close()

        events_by_date = {}
        for event in events:
            event_date = event[1]
            if event_date not in events_by_date:
                events_by_date[event_date] = []
            events_by_date[event_date].append(event)

        processed_events = {}

        for event in events:

            title = event[0]
            date = event[1]
            start = event[2]
            end = event[3]
            details = event[4]
            ID = event[5]

            start_dt = datetime.strptime(start, "%H:%M")
            end_dt = datetime.strptime(end, "%H:%M")

            start_minutes = (
                start_dt.hour * 60 +
                start_dt.minute
            )

            end_minutes = (
                end_dt.hour * 60 +
                end_dt.minute
            )

            processed_event = {
                "id": ID,
                "title": title,
                "date": date,
                "start": start,
                "end": end,
                "details": details,
                "top": start_minutes,
                "height": end_minutes - start_minutes
            }

            if date not in processed_events:
                processed_events[date] = []

            processed_events[date].append(processed_event)

        return processed_events
    except:
        return {}

def curr_scheduled_tasks(week_start):
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")

    conn = sqlite3.connect("tasks.db")
    try:
        rows = conn.execute("""
            SELECT id, title, assignedTo, createdBy, details, priority, status,
                   due_date, duration, scheduled_date, scheduled_start, scheduled_end
            FROM tasks
            WHERE scheduled = 1
            AND scheduled_date >= ?
            AND scheduled_date <= ?
        """, (week_start_str, week_end_str)).fetchall()
    except:
        rows = []
    conn.close()

    scheduled_by_date = {}

    for row in rows:
        (task_id, title, assignedTo, createdBy, details, priority, status,
         due_date, duration, sched_date, start, end) = row

        start_dt = datetime.strptime(start, "%H:%M")
        end_dt = datetime.strptime(end, "%H:%M")

        start_minutes = start_dt.hour * 60 + start_dt.minute
        end_minutes = end_dt.hour * 60 + end_dt.minute

        block = {
            "id": task_id,
            "title": title,
            "assignedTo": assignedTo,
            "createdBy": createdBy,
            "details": details,
            "priority": priority,
            "status": status,
            "due_date": due_date,
            "duration": duration,
            "date": sched_date,
            "start": start,
            "end": end,
            "top": start_minutes,
            "height": end_minutes - start_minutes
        }

        scheduled_by_date.setdefault(sched_date, []).append(block)

    return scheduled_by_date

def get_assignees():
    conn = sqlite3.connect("tasks.db")
    try:
        rows = conn.execute("""
        SELECT DISTINCT assignedTo
        FROM tasks
        ORDER BY assignedTo
    """).fetchall()
    except:
        return []
    conn.close()
    return [row[0] for row in rows]
    

# ------------------------
# Sleep schedule (per person)
# ------------------------

def _ensure_sleep_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sleep_schedule (
            person TEXT PRIMARY KEY,
            sleep_start TEXT NOT NULL DEFAULT '23:00',
            sleep_end TEXT NOT NULL DEFAULT '07:00'
        )
    """)

def get_sleep_window(person):
    conn = sqlite3.connect("tasks.db")
    _ensure_sleep_table(conn)
    row = conn.execute(
        "SELECT sleep_start, sleep_end FROM sleep_schedule WHERE person = ?",
        (person,)
    ).fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    # sensible default if the person hasn't set their own sleep hours
    return "23:00", "07:00"

def set_sleep_window(person, sleep_start, sleep_end):
    conn = sqlite3.connect("tasks.db")
    _ensure_sleep_table(conn)
    conn.execute("""
        INSERT INTO sleep_schedule(person, sleep_start, sleep_end)
        VALUES (?,?,?)
        ON CONFLICT(person) DO UPDATE SET
            sleep_start = excluded.sleep_start,
            sleep_end = excluded.sleep_end
    """, (person, sleep_start, sleep_end))
    conn.commit()
    conn.close()

# ------------------------
# Small time-math helpers
# ------------------------

def _time_to_minutes(t):
    dt = datetime.strptime(t, "%H:%M")
    return dt.hour * 60 + dt.minute

def _minutes_to_time(m):
    m = max(0, min(1439, m))
    return f"{m // 60:02d}:{m % 60:02d}"

def _merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]

def _free_slots(busy_intervals, day_start=0, day_end=1440):
    merged = _merge_intervals(busy_intervals)
    free = []
    cursor = day_start
    for s, e in merged:
        if s > cursor:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < day_end:
        free.append((cursor, day_end))
    return free

# ------------------------
# Auto-scheduling algorithm
#
# Places every unscheduled task into the earliest free slot
# that fits before its due date, considering (in order):
#   - existing events
#   - already-scheduled tasks (and tasks placed earlier in this run)
#   - the assignee's usual sleeping hours
#   - not scheduling anything in the past
#
# Tasks are placed earliest-due-date-first (ties broken by
# priority, then longer tasks first so they don't get starved
# of the few big gaps available).
# ------------------------

def optimize_schedule():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row

    unscheduled = conn.execute("""
        SELECT id, title, assignedTo, due_date, duration, priority
        FROM tasks
        WHERE scheduled = 0
        AND due_date IS NOT NULL
        AND due_date != ''
        AND duration IS NOT NULL
    """).fetchall()

    if not unscheduled:
        conn.close()
        return {"scheduled": [], "unscheduled": []}

    priority_rank = {"High": 0, "Medium": 1, "Low": 2}

    valid_tasks = []
    invalid_tasks = []
    for t in unscheduled:
        try:
            datetime.strptime(t["due_date"], "%Y-%m-%d")
            valid_tasks.append(t)
        except (ValueError, TypeError):
            invalid_tasks.append({"id": t["id"], "title": t["title"]})

    valid_tasks.sort(key=lambda t: (
        t["due_date"],
        priority_rank.get(t["priority"], 1),
        -t["duration"]
    ))

    now = datetime.now()
    today = now.date()
    today_str = today.strftime("%Y-%m-%d")

    horizon = max(
        [datetime.strptime(t["due_date"], "%Y-%m-%d").date() for t in valid_tasks] + [today]
    )

    date_strs = []
    d = today
    while d <= horizon:
        date_strs.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)

    first_str, last_str = date_strs[0], date_strs[-1]

    events_rows = conn.execute(
        "SELECT date, start, end FROM events WHERE date >= ? AND date <= ?",
        (first_str, last_str)
    ).fetchall()

    scheduled_rows = conn.execute("""
        SELECT scheduled_date, scheduled_start, scheduled_end
        FROM tasks
        WHERE scheduled = 1
        AND scheduled_date >= ?
        AND scheduled_date <= ?
    """, (first_str, last_str)).fetchall()

    busy_by_date = {ds: [] for ds in date_strs}

    for r in events_rows:
        if r["date"] in busy_by_date:
            busy_by_date[r["date"]].append(
                (_time_to_minutes(r["start"]), _time_to_minutes(r["end"]))
            )

    for r in scheduled_rows:
        if r["scheduled_date"] in busy_by_date:
            busy_by_date[r["scheduled_date"]].append(
                (_time_to_minutes(r["scheduled_start"]), _time_to_minutes(r["scheduled_end"]))
            )

    sleep_cache = {}
    scheduled_results = []
    unscheduled_results = list(invalid_tasks)

    for t in valid_tasks:
        person = t["assignedTo"]
        duration = t["duration"]
        due_date = t["due_date"]

        if person not in sleep_cache:
            sleep_cache[person] = get_sleep_window(person)
        sleep_start, sleep_end = sleep_cache[person]

        sleep_start_min = _time_to_minutes(sleep_start)
        sleep_end_min = _time_to_minutes(sleep_end)

        placed = False

        for ds in date_strs:
            # never schedule a task after its due date
            if due_date >= today_str and ds > due_date:
                break

            day_date = datetime.strptime(ds, "%Y-%m-%d").date()

            busy = list(busy_by_date[ds])

            if sleep_start_min > sleep_end_min:
                # overnight sleep window (e.g. 23:00 -> 07:00)
                busy.append((sleep_start_min, 1440))
                busy.append((0, sleep_end_min))
            elif sleep_start_min < sleep_end_min:
                busy.append((sleep_start_min, sleep_end_min))

            if day_date == today:
                minutes_now = now.hour * 60 + now.minute
                minutes_now = ((minutes_now // 15) + 1) * 15
                busy.append((0, minutes_now))

            for free_start, free_end in _free_slots(busy):
                if free_end - free_start >= duration:
                    start_min = free_start
                    end_min = free_start + duration
                    start_str = _minutes_to_time(start_min)
                    end_str = _minutes_to_time(end_min)

                    conn.execute("""
                        UPDATE tasks
                        SET scheduled_date = ?,
                            scheduled_start = ?,
                            scheduled_end = ?,
                            scheduled = 1
                        WHERE id = ?
                    """, (ds, start_str, end_str, t["id"]))

                    busy_by_date[ds].append((start_min, end_min))

                    scheduled_results.append({
                        "id": t["id"],
                        "title": t["title"],
                        "date": ds,
                        "start": start_str,
                        "end": end_str
                    })
                    placed = True
                    break

            if placed:
                break

        if not placed:
            unscheduled_results.append({"id": t["id"], "title": t["title"]})

    conn.commit()
    conn.close()

    return {"scheduled": scheduled_results, "unscheduled": unscheduled_results}


app = Flask(__name__)
@app.route("/")
def homepage():
    return render_template("homepage.html", assignees = get_assignees())

@app.route("/tasks/")
def view_tasks():
    person = request.args.get("person", "").strip()
    if person:
        low, medium, high = find_tasks_indiv(person)
    else:
        low, medium, high = all_tasks()
    return render_template("tasklist.html", low=low, medium=medium, high=high, person=person)

@app.route("/createtask/", methods = ["GET", "POST"])
def createtask():
    if request.method == "GET":
        return render_template("createtask.html")
    
    title = request.form["title"]
    assignedTo = request.form["assignedTo"]
    createdBy = request.form["createdBy"]
    details = request.form["details"]
    due_date = request.form["due_date"]
    duration = int(request.form["duration"])
    
    if title.strip() == "":
        return "Task title cannot be empty."
    if assignedTo.strip() == "":
        return "Assigned To cannot be empty."
    if createdBy.strip() == "":
        return "Created By cannot be empty."
    if due_date == "":
        return "Please choose a due date."
    if duration <= 0:
        return "Duration must be positive."
    
    insert_task(title, assignedTo, createdBy, details, due_date, duration)
    return redirect(url_for("homepage"))


@app.route("/update_status/", methods=["POST"])
def update_status_route():
    data = request.get_json()
    ID = data["id"]
    status = data["status"]
    update_status(ID, status)
    return "", 204

@app.route("/update_priority/", methods=["POST"])
def update_priority_route():
    data = request.get_json()
    ID = data["id"]
    priority = data["priority"]
    update_priority(ID, priority)
    return "", 204

@app.route("/delete_task/", methods=["POST"])
def delete_task():
    if request.is_json:
        data = request.get_json()
        task_id = data.get("id")
    else:
        task_id = request.form["id"]

    conn = sqlite3.connect("tasks.db")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    if request.is_json:
        return "", 204
    return redirect(request.referrer)

@app.route("/update_task/", methods=["POST"])
def update_task_route():
    data = request.get_json()
    task_id = data.get("id")

    if not task_id:
        return {"success": False, "error": "Missing task id."}, 400

    title = (data.get("title") or "").strip()
    assignedTo = (data.get("assignedTo") or "").strip()
    createdBy = (data.get("createdBy") or "").strip()
    details = data.get("details", "")
    due_date = data.get("due_date", "")
    duration = data.get("duration")
    priority = data.get("priority")
    status = data.get("status")

    if title == "":
        return {"success": False, "error": "Task title cannot be empty."}, 400
    if assignedTo == "":
        return {"success": False, "error": "Assigned To cannot be empty."}, 400
    if createdBy == "":
        return {"success": False, "error": "Created By cannot be empty."}, 400
    if due_date == "":
        return {"success": False, "error": "Please choose a due date."}, 400

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        return {"success": False, "error": "Duration must be a number."}, 400

    if duration <= 0:
        return {"success": False, "error": "Duration must be positive."}, 400

    conn = sqlite3.connect("tasks.db")

    row = conn.execute(
        "SELECT scheduled, scheduled_start FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.execute("""
        UPDATE tasks
        SET title = ?, assignedTo = ?, createdBy = ?, details = ?,
            due_date = ?, duration = ?,
            priority = COALESCE(?, priority),
            status = COALESCE(?, status)
        WHERE id = ?
    """, (title, assignedTo, createdBy, details, due_date, duration, priority, status, task_id))

    # Keep the scheduled block's end time consistent if duration changed
    if row and row[0] == 1 and row[1]:
        start_dt = datetime.strptime(row[1], "%H:%M")
        new_end = (start_dt + timedelta(minutes=duration)).strftime("%H:%M")
        conn.execute("UPDATE tasks SET scheduled_end = ? WHERE id = ?", (new_end, task_id))

    conn.commit()
    conn.close()

    return {"success": True}, 200

@app.route("/calendar/")
def display_calendar():
    hours = [f"{i:02d}:00" for i in range(24)]
    offset = int(request.args.get("offset", 0))
    week, title = curr_week(offset)
    
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    current_sunday = (today - timedelta(days=days_since_sunday))
    week_start = (current_sunday + timedelta(weeks=offset))
    week = [week_start + timedelta(days=i) for i in range(7)]

    events = curr_events(week_start)
    scheduled_tasks = curr_scheduled_tasks(week_start)
    
    return render_template("calendar.html", hours = hours, week = week, events = events, title = title, offset = offset, tasks=get_unscheduled_tasks(), scheduled_tasks = scheduled_tasks)


@app.route("/addEvent/", methods = ["GET", "POST"])
def add_event():
    if request.method == "GET":
        return render_template("addevent.html")
    title = request.form["title"]
    date = request.form["date"]
    start = request.form["startTime"]
    end = request.form["endTime"]
    details = request.form["eventDetails"]
    
    conn = sqlite3.connect("tasks.db")
    overlap = conn.execute("""
    SELECT 1
    FROM events
    WHERE date=?
    AND start < ?
    AND end > ?
    """,
    (
        date,
        end,
        start
    )).fetchone()

    conn.close()
    if overlap:
        return "Another event already exists during this time."
    
    if title.strip() == "":
        return "Title required."
    if date == "":
        return "Date required."
    if start == "" or end == "":
        return "Start and end times required."
    if end <= start:
        return "End time must be after start time."
    
    event_datetime = datetime.strptime(
    f"{date} {start}",
    "%Y-%m-%d %H:%M")
    if event_datetime < datetime.now():
        return "This event is in the past."
    
    create_event(title, date, start, end, details)
    
    return redirect(url_for("display_calendar"))

@app.route("/delete_event/", methods=["POST"])
def delete_event():
    event_id = request.form["id"]
    conn = sqlite3.connect("tasks.db")
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

from flask import request

@app.route("/update_event/", methods=["POST"])
def update_event():
    data = request.get_json()
    conn = sqlite3.connect("tasks.db")
    conn.execute(
        """
        UPDATE events
        SET
            title = ?,
            date = ?,
            start = ?,
            end = ?,
            details = ?
        WHERE id = ?
        """,
        (
            data["title"],
            data["date"],
            data["start"],
            data["end"],
            data["details"],
            data["id"]
        )
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.route("/schedule_task/", methods=["POST"])
def schedule_task():
    data = request.json
    task_id = data["id"]
    date = data["date"]
    start = data["start"]

    conn = sqlite3.connect("tasks.db")
    duration = conn.execute(
        "SELECT duration FROM tasks WHERE id=?",
        (task_id,)
    ).fetchone()[0]

    start_dt = datetime.strptime(start, "%H:%M")
    end_dt = start_dt + timedelta(minutes=duration)
    end = end_dt.strftime("%H:%M")

    # Reject scheduling before the current time never mind timezone edge cases here;
    # main goal: prevent overlaps with existing events and other scheduled tasks.

    event_overlap = conn.execute(
        """
        SELECT 1
        FROM events
        WHERE date = ?
        AND start < ?
        AND end > ?
        """,
        (date, end, start)
    ).fetchone()

    task_overlap = conn.execute(
        """
        SELECT 1
        FROM tasks
        WHERE scheduled = 1
        AND id != ?
        AND scheduled_date = ?
        AND scheduled_start < ?
        AND scheduled_end > ?
        """,
        (task_id, date, end, start)
    ).fetchone()

    if event_overlap or task_overlap:
        conn.close()
        return {
            "success": False,
            "error": "This time slot overlaps with an existing event or task."
        }, 409

    conn.execute(
        """
        UPDATE tasks
        SET
            scheduled_date=?,
            scheduled_start=?,
            scheduled_end=?,
            scheduled=1
        WHERE id=?
        """,
        (
            date,
            start,
            end,
            task_id
        )
    )

    conn.commit()
    conn.close()

    return {"success": True}, 200

@app.route("/unschedule_task/", methods=["POST"])
def unschedule_task():
    data = request.get_json()
    task_id = data["id"]

    conn = sqlite3.connect("tasks.db")
    conn.execute(
        """
        UPDATE tasks
        SET
            scheduled=0,
            scheduled_date=NULL,
            scheduled_start=NULL,
            scheduled_end=NULL
        WHERE id=?
        """,
        (task_id,)
    )
    conn.commit()
    conn.close()

    return "", 204
    

@app.route("/optimize_schedule/", methods=["POST"])
def optimize_schedule_route():
    result = optimize_schedule()
    return result, 200

if __name__ == "__main__":
    app.run()
