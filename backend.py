from flask import Flask, redirect, url_for, render_template, request
import sqlite3, calendar
from datetime import date, datetime, timedelta

def insert_task(title, assignedTo, createdBy, details):
    conn = sqlite3.connect("tasks.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title, assignedTo, createdBy, details, priority, status)")
    conn.execute("INSERT INTO tasks(title, assignedTo, createdBy, details, priority, status) VALUES (?,?,?,?,?,?)", (title, assignedTo, createdBy, details, "Medium", "Not started"))
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

def create_event(title, date, start, end, details, category, due_date):
    conn = sqlite3.connect("tasks.db")
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, title, date, start, end, category, due_date, details)")
    conn.execute("INSERT INTO events(title, date, start, end, details, category, due_date) VALUES (?,?,?,?,?)", (title, date, start, end, details, category, due_date))
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

def curr_events():
    today = datetime.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = (week_start + timedelta(days=6)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect("tasks.db")
    events = conn.execute("SELECT title, date, start, end, details FROM events WHERE date >= ? AND date <= ? ORDER BY date, start", (week_start_str, week_end_str)).fetchall()
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
    

app = Flask(__name__)
@app.route("/", methods = ["GET", "POST"])
def homepage():
    if request.method == "GET":
        return render_template("homepage.html")
    query = request.form["search"]
    query = query.strip()
    if query.lower() == "all":
        low, medium, high = all_tasks()
        return render_template("tasklist.html", low=low, medium=medium, high=high)
    else:
        low, medium, high = find_tasks_indiv(query)
        return render_template("tasklist.html", low=low, medium=medium, high=high)
    

@app.route("/createtask/", methods = ["GET", "POST"])
def createtask():
    if request.method == "GET":
        return render_template("createtask.html")
    title = request.form["title"]
    assignedTo = request.form["assignedTo"]
    createdBy = request.form["createdBy"]
    details = request.form["details"]
    insert_task(title, assignedTo, createdBy, details)
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

@app.route("/calendar/")
def display_calendar():
    hours = [f"{i:02d}:00" for i in range(24)]
    offset = int(request.args.get("offset", 0))
    week, title = curr_week(offset)
    events = curr_events()
    return render_template("calendar.html", hours = hours, week = week, events = events, title = title, offset = offset)

@app.route("/addEvent/", methods = ["GET", "POST"])
def add_event():
    if request.method == "GET":
        return render_template("addevent.html")
    title = request.form["title"]
    date = request.form["date"]
    start = request.form["startTime"]
    end = request.form["endTime"]
    details = request.form["eventDetails"]
    create_event(title, date, start, end, details)
    return redirect(url_for("display_calendar"))

if __name__ == "__main__":
    app.run()
