import tkinter as tk
from tkinter import ttk, messagebox
from time import strftime
from datetime import datetime
from zoneinfo import ZoneInfo
import webbrowser
from io import BytesIO
import urllib.request
from PIL import Image, ImageTk,ImageOps,ImageDraw

# External library for battery and notification
import psutil
from plyer import notification

position = "700+70"

# ------------------------------------ Global Configuration variable --------------------------
current_format = "%I:%M"  # Default 12-hour format
show_ampm = True
always_on_top = False
is_mini_mode = False  # Mini mode tracking

# theme color configuration
current_bg = "#121e26"
current_fg = "#00d4ff"
current_sec_fg = "#5dade2"
current_footer_fg = "#7fb3d5"

# Font configuration
selected_font_family = "Arial"

# Hourly chime tracking
last_chime_hour = -1

# reminder database (Memory)
reminders = {}  # Format: {"YYYY-MM-DD": ["Event 1", "Event 2"]}

def update_time():
    global current_format, show_ampm, last_chime_hour

    now_time = datetime.now()

    # Hourly Chime Login
    if now_time.minute == 0 and now_time.second == 0 and now_time.hour != last_chime_hour:
        last_chime_hour = now_time.hour
        trigger_hourly_chime(now_time.strftime("%I:00 %p"))

    # reminder check
    if now_time.hour == 0 and now_time.minute == 0 and now_time.second == 0:
        check_daily_reminders()

    # Main clock time update
    time_string = strftime(current_format)
    seconds_string = strftime("%S")
    am_pm = strftime("%p") if show_ampm else ""
    day_string = strftime("%A").upper()
    date_string = strftime("%b %d, %Y")

    time_label.config(text=time_string)
    sec_label.config(text=seconds_string)
    ampm_label.config(text=am_pm)
    day_label.config(text=day_string)
    date_label.config(text=date_string)

    # Battery and system monitor update
    update_battery_status()

    # Checking alarms in the background
    check_alarms()

    time_label.after(1000, update_time)


# ---------------------------------------- Hourly Chime functionality ------------------------------
def trigger_hourly_chime(current_hour_str):
    try:
        notification.notify(
            title="Hourly Chime",
            message=f"⏰ It's now {current_hour_str}. Keep up the great work!",
            app_name="Digital Clock",
            timeout=5
        )
        root.bell()
    except Exception:
        pass


# ------------------------------------ Battery & System Monitor --------------------------
def update_battery_status():
    try:
        battery = psutil.sensors_battery()
        percent = battery.percent
        is_charging = battery.power_plugged

        status_str = f"🔋 {percent}%"
        if is_charging:
            status_str += " (Charging)"

        battery_label.config(text=status_str)
    except Exception:
        battery_label.config(text="🔋 Battery N/A")


# --------------------------- Customizable Font Styles --------------------------
def change_font(font_name):
    global selected_font_family
    selected_font_family = font_name

    if is_mini_mode:
        time_label.config(font=(selected_font_family, 30, "bold"))
    else:
        time_label.config(font=(selected_font_family, 110, "bold"))

    day_label.config(font=(selected_font_family, 15, "bold"))
    sec_label.config(font=(selected_font_family, 45, "bold"))
    ampm_label.config(font=(selected_font_family, 22, "bold"))
    date_label.config(font=(selected_font_family, 18))


# ---------------------------------- Event/Birthday Reminder --------------------------------
def open_reminder_manager():
    rem_window = tk.Toplevel(root)
    rem_window.title("Event & Birthday Reminder")
    rem_window.geometry(f"450x350+{position}")
    rem_window.iconbitmap("./logo.ico")
    rem_window.configure(bg=current_bg)
    rem_window.attributes("-alpha", 0.85)

    input_frame = tk.Frame(rem_window, bg=current_bg)
    input_frame.pack(pady=10)

    tk.Label(input_frame, text="Date (YYYY-MM-DD):", font=("Arial", 10), bg=current_bg, fg="#fff").grid(row=0, column=0, padx=5, pady=5)
    date_entry = tk.Entry(input_frame, width=15, font=("Arial", 10))
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    date_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(input_frame, text="Event / Note:", font=("Arial", 10), bg=current_bg, fg="#fff").grid(row=1, column=0, padx=5, pady=5)
    event_entry = tk.Entry(input_frame, width=25, font=("Arial", 10))
    event_entry.grid(row=1, column=1, padx=5, pady=5)

    list_frame = tk.Frame(rem_window, bg=current_bg)
    list_frame.pack(pady=10, fill="both", expand=True, padx=20)

    rem_box = tk.Listbox(list_frame, font=("Arial", 10), bg="#1c2d37", fg=current_fg, selectbackground="#5dade2")
    rem_box.pack(side="left", fill="both", expand=True)

    def refresh_list():
        rem_box.delete(0, tk.END)
        for d, ev_list in reminders.items():
            for ev in ev_list:
                rem_box.insert(tk.END, f"[{d}] {ev}")

    refresh_list()

    def add_reminder():
        d_str = date_entry.get().strip()
        e_str = event_entry.get().strip()
        if d_str and e_str:
            try:
                datetime.strptime(d_str, "%Y-%m-%d")
                if d_str not in reminders:
                    reminders[d_str] = []
                reminders[d_str].append(e_str)
                refresh_list()
                event_entry.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Use Correct Date Format (YYYY-MM-DD)")
        else:
            messagebox.showwarning("Warning", "Fields cannot be empty!")

    tk.Button(input_frame, text="Save Reminder", font=("Arial", 9, "bold"), bg="#5dade2", fg="#121e26", command=add_reminder).grid(row=2, column=1, sticky="e", pady=5)

def check_daily_reminders():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if today_str in reminders:
        events = "\n".join([f"- {e}" for e in reminders[today_str]])
        messagebox.showinfo("Today's Reminders & Birthdays", f"📅 Today's Events:\n{events}")


# -------------------------------- Mini Mode / Compact View ----------------------------------
def toggle_mini_mode():
    global is_mini_mode
    is_mini_mode = not is_mini_mode

    if is_mini_mode:
        root.geometry("300x80")
        day_label.pack_forget()
        sec_frame.pack_forget()
        footer_frame.pack_forget()
        time_label.config(font=(selected_font_family, 32, "bold"))
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
    else:
        root.geometry("650x370")
        day_label.pack(anchor="nw", padx=10)
        time_label.config(font=(selected_font_family, 110, "bold"))
        sec_frame.pack(side="left", padx=15, pady=(45, 0))
        footer_frame.pack(fill="x", padx=10, pady=10)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")


# -------------------------- Previous stopwatch functionality -------------------------
stopwatch_running = False
counter = 0

def open_stopwatch():
    stopwatch_window = tk.Toplevel(root)
    stopwatch_window.title("Stopwatch")
    stopwatch_window.iconbitmap("./logo.ico")
    stopwatch_window.geometry(f"350x200+{position}")
    stopwatch_window.configure(bg=current_bg)
    stopwatch_window.attributes("-alpha", 0.85)

    global stopwatch_running, counter
    stopwatch_running = False
    counter = 0

    def counter_label(label):
        def count():
            if stopwatch_running:
                global counter
                counter += 1
                mins, secs = divmod(counter // 10, 60)
                hours, mins = divmod(mins, 60)
                h_str = f"{hours:02d}:" if hours > 0 else ""
                label.config(text=f"{h_str}{mins:02d}:{secs:02d}:{counter % 10}")
                label.after(100, count)
        count()

    def start():
        global stopwatch_running
        if not stopwatch_running:
            stopwatch_running = True
            counter_label(sw_label)

    def pause():
        global stopwatch_running
        stopwatch_running = False

    def reset():
        global counter, stopwatch_running
        stopwatch_running = False
        counter = 0
        sw_label.config(text="00:00:0")

    sw_label = tk.Label(stopwatch_window, text="00:00:0", font=("Arial", 40, "bold"), bg=current_bg, fg=current_fg)
    sw_label.pack(pady=20)

    btn_frame = tk.Frame(stopwatch_window, bg=current_bg)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Start", font=("Arial", 11, "bold"), bg="#5dade2", fg="#121e26", width=6, command=start).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Pause", font=("Arial", 11, "bold"), bg="#7fb3d5", fg="#121e26", width=6, command=pause).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Reset", font=("Arial", 11, "bold"), bg="#4682b4", fg="#121e26", width=6, command=reset).pack(side="left", padx=5)


# ------------------------- Previous world clock functionality ------------------------
def show_world_time(city_name, timezone_str):
    wc_window = tk.Toplevel(root)
    wc_window.title(f"{city_name} Time")
    wc_window.iconbitmap("./logo.ico")
    wc_window.geometry(f"420x180+{position}")
    wc_window.configure(bg=current_bg)
    wc_window.attributes("-alpha", 0.85)

    title_label = tk.Label(wc_window, text=f"{city_name}", font=("Arial", 12, "bold"), bg=current_bg, fg=current_footer_fg)
    title_label.pack(pady=10)

    wc_time_label = tk.Label(wc_window, font=("Arial", 35, "bold"), bg=current_bg, fg=current_fg)
    wc_time_label.pack()

    wc_date_label = tk.Label(wc_window, font=("Arial", 14), bg=current_bg, fg=current_sec_fg)
    wc_date_label.pack(pady=5)

    def update_world_time():
        global current_format, show_ampm
        try:
            now = datetime.now(ZoneInfo(timezone_str))
            if current_format == "%I:%M":
                wc_format = "%I:%M:%S %p"
            else:
                wc_format = "%H:%M:%S"

            time_str = now.strftime(wc_format)
            date_str = now.strftime("%A, %b %d, %Y")

            wc_time_label.config(text=time_str)
            wc_date_label.config(text=date_str)
            wc_time_label.after(1000, update_world_time)
        except Exception:
            wc_time_label.config(text="Error loading time", font=("Arial", 18))

    update_world_time()


# ----------------------------- Previous alarm functionality -------------------------------
alarm_list = []

def open_alarm_manager():
    alarm_window = tk.Toplevel(root)
    alarm_window.title("Alarm Manager")
    alarm_window.iconbitmap("./logo.ico")
    alarm_window.geometry(f"400x350+{position}")
    alarm_window.configure(bg=current_bg)
    alarm_window.attributes("-alpha", 0.85)

    input_frame = tk.Frame(alarm_window, bg=current_bg)
    input_frame.pack(pady=15)

    hours = [f"{i:02d}" for i in range(1, 13)]
    minutes = [f"{i:02d}" for i in range(0, 60)]
    periods = ["AM", "PM"]

    hr_cb = ttk.Combobox(input_frame, values=hours, width=3, font=("Arial", 12), state="readonly")
    hr_cb.set("12")
    hr_cb.pack(side="left", padx=2)

    tk.Label(input_frame, text=":", font=("Arial", 12, "bold"), bg=current_bg, fg="#fff").pack(side="left")

    min_cb = ttk.Combobox(input_frame, values=minutes, width=3, font=("Arial", 12), state="readonly")
    min_cb.set("00")
    min_cb.pack(side="left", padx=2)

    period_cb = ttk.Combobox(input_frame, values=periods, width=4, font=("Arial", 12), state="readonly")
    period_cb.set("AM")
    period_cb.pack(side="left", padx=5)

    list_frame = tk.Frame(alarm_window, bg=current_bg)
    list_frame.pack(pady=10, fill="both", expand=True, padx=20)

    alarm_box = tk.Listbox(list_frame, font=("Arial", 12), bg="#1c2d37", fg=current_fg, selectbackground="#5dade2")
    alarm_box.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=alarm_box.yview)
    scrollbar.pack(side="right", fill="y")
    alarm_box.config(yscrollcommand=scrollbar.set)

    for alarm in alarm_list:
        alarm_box.insert(tk.END, alarm)

    def add_alarm():
        alarm_time = f"{hr_cb.get()}:{min_cb.get()} {period_cb.get()}"
        if alarm_time not in alarm_list:
            alarm_list.append(alarm_time)
            alarm_box.insert(tk.END, alarm_time)
        else:
            messagebox.showwarning("Warning", "This alarm is already set!")

    def delete_alarm():
        try:
            selected_index = alarm_box.curselection()[0]
            selected_alarm = alarm_box.get(selected_index)
            alarm_list.remove(selected_alarm)
            alarm_box.delete(selected_index)
        except IndexError:
            messagebox.showwarning("Warning", "Please select an alarm to delete.")

    btn_frame = tk.Frame(alarm_window, bg=current_bg)
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text="Add Alarm", font=("Arial", 11, "bold"), bg="#5dade2", fg="#121e26", command=add_alarm).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Delete Selected", font=("Arial", 11, "bold"), bg="#e74c3c", fg="#fff", command=delete_alarm).pack(side="left", padx=10)

def check_alarms():
    current_time_str = strftime("%I:%M %p")
    current_sec = strftime("%S")
    if current_sec == "00" and current_time_str in alarm_list:
        messagebox.showinfo("Alarm", f"Wake Up! It's {current_time_str}!")


# ------------------------------------ Countdown Timer ---------------------------------------
timer_running = False
timer_seconds = 0

def open_timer():
    timer_window = tk.Toplevel(root)
    timer_window.title("Countdown Timer")
    timer_window.iconbitmap("./logo.ico")
    timer_window.geometry(f"350x220+{position}")
    timer_window.configure(bg=current_bg)
    timer_window.attributes("-alpha", 0.85)

    global timer_running
    timer_running = False

    input_frame = tk.Frame(timer_window, bg=current_bg)
    input_frame.pack(pady=10)

    hrs_vals = [f"{i:02d}" for i in range(24)]
    mins_vals = [f"{i:02d}" for i in range(60)]

    hr_cb = ttk.Combobox(input_frame, values=hrs_vals, width=3, font=("Arial", 12), state="readonly")
    hr_cb.set("00")
    hr_cb.pack(side="left", padx=2)

    min_cb = ttk.Combobox(input_frame, values=mins_vals, width=3, font=("Arial", 12), state="readonly")
    min_cb.set("05")
    min_cb.pack(side="left", padx=2)

    sec_cb = ttk.Combobox(input_frame, values=mins_vals, width=3, font=("Arial", 12), state="readonly")
    sec_cb.set("00")
    sec_cb.pack(side="left", padx=2)

    display_label = tk.Label(timer_window, text="00:05:00", font=("Arial", 35, "bold"), bg=current_bg, fg=current_fg)
    display_label.pack(pady=10)

    def count_down():
        global timer_seconds, timer_running
        if timer_running and timer_seconds > 0:
            timer_seconds -= 1
            h, rem = divmod(timer_seconds, 3600)
            m, s = divmod(rem, 60)
            display_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
            display_label.after(1000, count_down)
        elif timer_running and timer_seconds == 0:
            timer_running = False
            messagebox.showinfo("Timer Ended", "Time is up!")

    def start_timer():
        global timer_seconds, timer_running
        if not timer_running:
            h = int(hr_cb.get())
            m = int(min_cb.get())
            s = int(sec_cb.get())
            timer_seconds = (h * 3600) + (m * 60) + s
            if timer_seconds > 0:
                timer_running = True
                count_down()

    def stop_timer():
        global timer_running
        timer_running = False

    btn_frame = tk.Frame(timer_window, bg=current_bg)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Start", font=("Arial", 11, "bold"), bg="#5dade2", fg="#121e26", command=start_timer).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Stop", font=("Arial", 11, "bold"), bg="#e74c3c", fg="#fff", command=stop_timer).pack(side="left", padx=5)


# --- Pomodoro Tracker ---
pomo_running = False
pomo_seconds = 25 * 60
is_break = False

def open_pomodoro():
    pomo_window = tk.Toplevel(root)
    pomo_window.title("Pomodoro Tracker")
    pomo_window.iconbitmap("./logo.ico")
    pomo_window.geometry(f"350x220+{position}")
    pomo_window.configure(bg=current_bg)
    pomo_window.attributes("-alpha", 0.85)

    global pomo_running, pomo_seconds, is_break
    pomo_running = False
    pomo_seconds = 25 * 60
    is_break = False

    status_label = tk.Label(pomo_window, text="Work Session", font=("Arial", 16, "bold"), bg=current_bg, fg="#e74c3c")
    status_label.pack(pady=10)

    display_label = tk.Label(pomo_window, text="25:00", font=("Arial", 40, "bold"), bg=current_bg, fg=current_fg)
    display_label.pack(pady=5)

    def run_pomo():
        global pomo_seconds, pomo_running, is_break
        if pomo_running and pomo_seconds > 0:
            pomo_seconds -= 1
            m, s = divmod(pomo_seconds, 60)
            display_label.config(text=f"{m:02d}:{s:02d}")
            display_label.after(1000, run_pomo)
        elif pomo_running and pomo_seconds == 0:
            if not is_break:
                messagebox.showinfo("Pomodoro", "Work session over! Take a 5-minute break.")
                is_break = True
                status_label.config(text="Short Break", fg="#2ecc71")
                pomo_seconds = 5 * 60
            else:
                messagebox.showinfo("Pomodoro", "Break over! Get back to work.")
                is_break = False
                status_label.config(text="Work Session", fg="#e74c3c")
                pomo_seconds = 25 * 60
            run_pomo()

    def start_pomo():
        global pomo_running
        if not pomo_running:
            pomo_running = True
            run_pomo()

    def pause_pomo():
        global pomo_running
        pomo_running = False

    def reset_pomo():
        global pomo_running, pomo_seconds, is_break
        pomo_running = False
        is_break = False
        pomo_seconds = 25 * 60
        status_label.config(text="Work Session", fg="#e74c3c")
        display_label.config(text="25:00")

    btn_frame = tk.Frame(pomo_window, bg=current_bg)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Start", font=("Arial", 11, "bold"), bg="#2ecc71", fg="#fff", command=start_pomo).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Pause", font=("Arial", 11, "bold"), bg="#f39c12", fg="#fff", command=pause_pomo).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Reset", font=("Arial", 11, "bold"), bg="#e74c3c", fg="#fff", command=reset_pomo).pack(side="left", padx=5)


# --- Time Format Toggle ---
def toggle_time_format():
    global current_format, show_ampm
    if current_format == "%I:%M":
        current_format = "%H:%M"
        show_ampm = False
        messagebox.showinfo("Format Changed", "Switched to 24-Hour Format")
    else:
        current_format = "%I:%M"
        show_ampm = True
        messagebox.showinfo("Format Changed", "Switched to 12-Hour Format (AM/PM)")


# ------------------------------------------- Theme Customizer ------------------------------
def apply_theme(bg, fg, sec_fg, footer_fg):
    global current_bg, current_fg, current_sec_fg, current_footer_fg
    current_bg, current_fg, current_sec_fg, current_footer_fg = bg, fg, sec_fg, footer_fg

    root.configure(bg=bg)
    main_frame.configure(bg=bg)
    time_frame.configure(bg=bg)
    sec_frame.configure(bg=bg)
    footer_frame.configure(bg=bg)

    day_label.config(bg=bg, fg=footer_fg)
    time_label.config(bg=bg, fg=fg)
    sec_label.config(bg=bg, fg=sec_fg)
    ampm_label.config(bg=bg, fg=sec_fg)
    date_label.config(bg=bg, fg=footer_fg)
    tz_label.config(bg=bg, fg=footer_fg)
    battery_label.config(bg=bg, fg=sec_fg)

def set_opacity(val):
    root.attributes("-alpha", float(val))

def open_theme_customizer():
    theme_window = tk.Toplevel(root)
    theme_window.title("Theme Customizer")
    theme_window.iconbitmap("./logo.ico")
    theme_window.geometry(f"300x280+{position}")
    theme_window.configure(bg=current_bg)
    theme_window.attributes("-alpha", 0.85)

    tk.Label(theme_window, text="Select Color Theme", font=("Arial", 12, "bold"), bg=current_bg, fg="#fff").pack(pady=10)

    tk.Button(theme_window, text="Standard Dark Mode", width=20, bg="#121e26", fg="#00d4ff", command=lambda: apply_theme("#121e26", "#00d4ff", "#5dade2", "#7fb3d5")).pack(pady=4)
    tk.Button(theme_window, text="Light Mode", width=20, bg="#f0f3f4", fg="#2c3e50", command=lambda: apply_theme("#f0f3f4", "#2c3e50", "#7f8c8d", "#34495e")).pack(pady=4)
    tk.Button(theme_window, text="Neon Green Theme", width=20, bg="#050f05", fg="#39ff14", command=lambda: apply_theme("#050f05", "#39ff14", "#00ffcc", "#1df914")).pack(pady=4)
    tk.Button(theme_window, text="Neon Pink Theme", width=20, bg="#0f050f", fg="#ff007f", command=lambda: apply_theme("#0f050f", "#ff007f", "#da70d6", "#ff69b4")).pack(pady=4)

    tk.Label(theme_window, text="Adjust Window Transparency", font=("Arial", 10), bg=current_bg, fg="#fff").pack(pady=(15, 2))
    slider = tk.Scale(theme_window, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", bg=current_bg, fg="#fff", highlightthickness=0, command=set_opacity)
    slider.set(root.attributes("-alpha"))
    slider.pack(fill="x", padx=30)


# --- Screen Overlay / Floating Mode ---
def toggle_always_on_top():
    global always_on_top
    always_on_top = not always_on_top
    root.attributes("-topmost", always_on_top)
    status = "Enabled" if always_on_top else "Disabled"
    messagebox.showinfo("Screen Overlay", f"Always on Top {status}")

# ==================================================Info===================
def show_skills_window():
    """Clicking on the Skills button will open this new window."""
    skills_window = tk.Toplevel()
    skills_window.title("Developer Skills")
    skills_window.iconbitmap("./logo.ico")
    skills_window.geometry("500x350+700+200")
    skills_window.configure(bg="#f4f6f9")
    skills_window.resizable(False, False)

    # Header
    header = tk.Frame(skills_window, bg="#0f172a", height=50)
    header.pack(fill="x")
    tk.Label(header, text="🛠️ Technical Skills Matrix", font=("Segoe UI", 12, "bold"), fg="white",bg="#0f172a").pack(pady=12)

    # table frame
    table_frame = tk.Frame(skills_window, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Tkinter Treeview (table) style setup
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#1e293b")
    style.configure("Treeview", font=("Segoe UI", 10), rowheight=28, background="white", fieldbackground="white")

    # create column
    cols = ("Category", "Skills / Technologies")
    table = ttk.Treeview(table_frame, columns=cols, show="headings")

    table.heading("Category", text="Category")
    table.heading("Skills / Technologies", text="Skills / Technologies")

    table.column("Category", width=185, minwidth=100, anchor="w")
    # The column width has been increased slightly and scrolling is possible if there is a lot of text.
    table.column("Skills / Technologies", width=600, minwidth=300, anchor="w")

    skills_data = [
        ("Programming Languages", "Python, Rust, JavaScript, Go, C, C++, R, Java, Kotlin, TypeScript, Dart, PHP, SQL, Java"),
        ("AI & Deep Learning", "Neural Networks, FNN or ANN, CNNs,RNN, LSTM, GRU, Transformer, BERT, Large Language Models (LLMs)"),
        ("Data Science","Data Collection, Data Preprocessing, Data Analysis(EDA), Data Visualization"),
        ("Deap Learning Frameworks", "PyTorch, TensorFlow"),
        ("Machine Learning Frameworks","scikit-learn, XGBoost, LightGBM"),
        ("Web Development", "React (Frontend), Django, Express.js, Node.js (Backend)"),
        ("Mobile App Development", "Kotlin, Java, Flutter, React-Native, Jetpack Compose, XML, Room Database, Firebase, CRUD Operations"),
        ("Database","MySQL, PostgreSQL, SQLite, Microsoft SQL Server, MongoDB"),
        ("Tools & Platforms", "Git, GitHub, Docker, VS Code"),
        ("Operating Systems", "Windows, Linux (Kali Linux)")
    ]

    for index, (category, skills) in enumerate(skills_data):
        tag = "evenrow" if index % 2 == 0 else "oddrow"
        table.insert("", "end", values=(category, skills), tags=(tag,))

    table.tag_configure("evenrow", background="#f8fafc")
    table.tag_configure("oddrow", background="white")

    # --- Vertical scrollbar ---
    v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.pack(side="right", fill="y")

    # --- Adding a horizontal scrollbar ---
    h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
    table.configure(xscrollcommand=h_scrollbar.set)
    h_scrollbar.pack(side="bottom", fill="x")

    # Pack the table between the scrollbars
    table.pack(side="left", fill="both", expand=True)

    # --- Mouse and keyboard binding (for easier control) ---

    # Scroll up and down with the mouse wheel
    def on_mouse_wheel(event):
        table.yview_scroll(int(-1 * (event.delta / 120)), "units")
    table.bind("<MouseWheel>", on_mouse_wheel)

    # Scroll left and right with Shift + Mouse Wheel or Shift + Arrow Keys
    def on_horizontal_scroll(event):
        table.xview_scroll(int(-1 * (event.delta / 120)), "units")

    # In Windows, holding down the Shift key and turning the mouse wheel will scroll left and right.
    table.bind("<Shift-MouseWheel>", on_horizontal_scroll)


# ----------------------------- Function to crop any image into a round shape--------------
def make_circle_image(image_path_or_bytes, size=(90, 90)):
    """Function to crop any image into a round shape"""

    # Open the image and resize it to a specific size.
    img = Image.open(image_path_or_bytes).convert("RGBA")
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)

    # Creating a circular alpha mask
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)

    # Adding the mask to the alpha channel of the original image
    output = Image.new("RGBA", size, (0, 0, 0, 0))  # Transparent background
    output.paste(img, (0, 0), mask=mask)

    return output

def developer_info():
    window = tk.Toplevel(root)
    window.title("Developer Information")
    window.iconbitmap("./logo.ico")
    window.geometry("550x610+650+80")
    window.configure(bg="#f4f6f9")
    window.resizable(False, False)

    # --- Profile picture section ---
    image_source = "./my_img.jpg"
    try:
        if image_source.startswith("http://") or image_source.startswith("https://"):
            with urllib.request.urlopen(image_source) as url:
                img_to_open = BytesIO(url.read())
        else:
            img_to_open = image_source

        round_im = make_circle_image(img_to_open, size=(90, 90))
        profile_img = ImageTk.PhotoImage(round_im) if round_im else None
    except Exception as e:
        print("There was a problem loading the image:", e)
        profile_img = None

    # --- Main Card frame ---
    card_frame = tk.Frame(window, bg="white", bd=0, highlightbackground="#e0e0e0", highlightthickness=1)
    card_frame.place(x=25, y=20, width=500, height=540)

    # --- Header section ---
    header_frame = tk.Frame(card_frame, bg="#1e293b", height=50)
    header_frame.pack(fill="x", side="top")
    tk.Label(header_frame, text="DEVELOPER PROFILE", font=("Segoe UI", 13, "bold"), bg="#1e293b", fg="white").pack(pady=12)

    # --- Goal profile image ---
    img_label = tk.Label(card_frame, bg="white")
    if profile_img:
        img_label.config(image=profile_img)
        img_label.image = profile_img
    else:
        img_label.config(text="[ No Image ]", fg="gray", font=("Arial", 10))
    img_label.pack(pady=10)

    # --- Information container frame ---
    info_frame = tk.Frame(card_frame, bg="white")
    info_frame.pack(fill="both", expand=True, padx=45)

    def add_info_row(row_num, label_text, value_text):
        lbl = tk.Label(info_frame, text=label_text, font=("Segoe UI", 10, "bold"), bg="white", fg="#64748b", anchor="w")
        lbl.grid(row=row_num, column=0, sticky="w", pady=2)

        val = tk.Label(info_frame, text=value_text, font=("Segoe UI", 10), bg="white", fg="#0f172a", anchor="w")
        val.grid(row=row_num, column=1, sticky="w", padx=25, pady=2)

    add_info_row(0, "Developer Name:", "SM Atiqur Rahman Limon")
    add_info_row(1, "Phone:", "+8801321358921")
    add_info_row(2, "E-mail:", "scienceandtechnologylab24@gmail.com")
    add_info_row(3, "Profession:", "Student")
    add_info_row(4, "Institute:", "Barishal Polytechnic Institute")
    add_info_row(5, "Department:", "Computer Science & Technology")
    add_info_row(6, "Session:", "2023-2024")
    add_info_row(7, "Roll:", "840801")
    add_info_row(8, "Reg No.:", "1502339845")
    add_info_row(9, "District:", "Jhalakathi")
    add_info_row(10, "Upazila:", "Rajapur")

    # --- Newly added row number 12: Skill (as Text Button) ---
    lbl_skill = tk.Label(info_frame, text="Skills:", font=("Segoe UI", 10, "bold"), bg="white", fg="#64748b", anchor="w")
    lbl_skill.grid(row=11, column=0, sticky="w", pady=2)

    # Clickable text button (Link style)
    btn_skill = tk.Label(info_frame,text="My all skill ↗",font=("Segoe UI", 10, "underline", "bold"), bg="white",fg="#0284c7",cursor="hand2")
    btn_skill.grid(row=11, column=1, sticky="w", padx=25, pady=2)
    # Clicking will open a new window.
    btn_skill.bind("<Button-1>", lambda e: show_skills_window())

    # --- Github link section ---
    github_frame = tk.Frame(card_frame, bg="white")
    github_frame.pack(side="bottom", pady=12)

    tk.Label(github_frame, text="GitHub: ", font=("Segoe UI", 10, "bold"), bg="white", fg="#64748b").pack(side="left")
    gh_link = tk.Label(github_frame, text="www.github.com/scienceandtechnologylab", font=("Segoe UI", 10, "underline"), fg="#0284c7", bg="white", cursor="hand2")
    gh_link.pack(side="left")
    gh_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.github.com/scienceandtechnologylab"))

    # --- Footer bar ---
    footer = tk.Label(window, text="Copyright© 2026 by Newton", font=("Segoe UI", 8), bg="#0f172a", fg="#94a3b8")
    footer.place(x=0, y=585, width=550, height=25)


# ------------------------------------ Main window setup ------------------------------------------
root = tk.Tk()
root.title("Digital Clock")
root.geometry("650x370+20+20")
root.configure(bg=current_bg)
root.attributes("-alpha", 0.85)
root.iconbitmap("./logo.ico")

# ------------------------------------ Menubar architecture --------------------------------------
menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

tools_menu = tk.Menu(menubar, tearoff=0)
tools_menu.add_command(label="Stopwatch", command=open_stopwatch)
tools_menu.add_command(label="Alarm Manager", command=open_alarm_manager)
tools_menu.add_command(label="Countdown Timer", command=open_timer)
tools_menu.add_command(label="Pomodoro Tracker", command=open_pomodoro)
tools_menu.add_command(label="Event/Birthday Reminder", command=open_reminder_manager)
tools_menu.add_separator()
tools_menu.add_command(label="Compact / Mini Mode", command=toggle_mini_mode)
tools_menu.add_command(label="Toggle 12/24 Hour", command=toggle_time_format)
tools_menu.add_command(label="Theme Customizer", command=open_theme_customizer)
tools_menu.add_command(label="Floating Mode (On/Off)", command=toggle_always_on_top)
tools_menu.add_separator()

# Customizable Font Styles sub-menu
font_menu = tk.Menu(tools_menu, tearoff=0)
font_menu.add_command(label="Standard Arial", command=lambda: change_font("Arial"))
font_menu.add_command(label="Classic Times New Roman", command=lambda: change_font("Times New Roman"))
font_menu.add_command(label="Futuristic Courier New", command=lambda: change_font("Courier New"))
font_menu.add_command(label="Modern Comic Sans", command=lambda: change_font("Comic Sans MS"))
font_menu.add_command(label="Impact bold style", command=lambda: change_font("Impact"))
tools_menu.add_cascade(label="Font Style Customizer", menu=font_menu)


# ------------------- World clock database with nearly 100 global cities --------------------
world_clock_menu = tk.Menu(tools_menu, tearoff=0)
world_cities = {
    "Asia (দক্ষিণ ও দক্ষিণ-পূর্ব)": [
        ("Dhaka (Capital), Bangladesh", "Asia/Dhaka"),
        ("Chittagong (Major), Bangladesh", "Asia/Dhaka"),
        ("New Delhi (Capital), India", "Asia/Kolkata"),
        ("Mumbai (Major), India", "Asia/Kolkata"),
        ("Kolkata (Major), India", "Asia/Kolkata"),
        ("Chennai (Major), India", "Asia/Kolkata"),
        ("Islamabad (Capital), Pakistan", "Asia/Karachi"),
        ("Karachi (Major), Pakistan", "Asia/Karachi"),
        ("Kathmandu (Capital), Nepal", "Asia/Kathmandu"),
        ("Colombo (Capital), Sri Lanka", "Asia/Colombo"),
        ("Thimphu (Capital), Bhutan", "Asia/Thimphu"),
        ("Kabul (Capital), Afghanistan", "Asia/Kabul"),
        ("Bangkok (Capital), Thailand", "Asia/Bangkok"),
        ("Singapore (Capital), Singapore", "Asia/Singapore"),
        ("Kuala Lumpur (Capital), Malaysia", "Asia/Kuala_Lumpur"),
        ("Jakarta (Capital), Indonesia", "Asia/Jakarta"),
        ("Manila (Capital), Philippines", "Asia/Manila"),
        ("Hanoi (Capital), Vietnam", "Asia/Ho_Chi_Minh"),
        ("Phnom Penh (Capital), Cambodia", "Asia/Phnom_Penh"),
        ("Yangon (Major), Myanmar", "Asia/Yangon")
    ],
    "Asia (পূর্ব ও মধ্য এশিয়া)": [
        ("Tokyo (Capital), Japan", "Asia/Tokyo"),
        ("Osaka (Major), Japan", "Asia/Tokyo"),
        ("Beijing (Capital), China", "Asia/Shanghai"),
        ("Shanghai (Major), China", "Asia/Shanghai"),
        ("Hong Kong (Major), China", "Asia/Hong_Kong"),
        ("Seoul (Capital), South Korea", "Asia/Seoul"),
        ("Taipei (Capital), Taiwan", "Asia/Taipei"),
        ("Ulaanbaatar (Capital), Mongolia", "Asia/Ulaanbaatar"),
        ("Tashkent (Capital), Uzbekistan", "Asia/Tashkent"),
        ("Almaty (Major), Kazakhstan", "Asia/Almaty")
    ],
    "Middle East (মধ্যপ্রাচ্য)": [
        ("Riyadh (Capital), Saudi Arabia", "Asia/Riyadh"),
        ("Mecca (Major), Saudi Arabia", "Asia/Riyadh"),
        ("Medina (Major), Saudi Arabia", "Asia/Riyadh"),
        ("Dubai (Major), UAE", "Asia/Dubai"),
        ("Abu Dhabi (Capital), UAE", "Asia/Dubai"),
        ("Doha (Capital), Qatar", "Asia/Qatar"),
        ("Kuwait City (Capital), Kuwait", "Asia/Kuwait"),
        ("Muscat (Capital), Oman", "Asia/Muscat"),
        ("Manama (Capital), Bahrain", "Asia/Bahrain"),
        ("Baghdad (Capital), Iraq", "Asia/Baghdad"),
        ("Tehran (Capital), Iran", "Asia/Tehran"),
        ("Jerusalem (Capital), Israel", "Asia/Jerusalem"),
        ("Beirut (Capital), Lebanon", "Asia/Beirut"),
        ("Amman (Capital), Jordan", "Asia/Amman")
    ],
    "Europe (ইউরোপ - ১)": [
        ("London (Capital), UK", "Europe/London"),
        ("Manchester (Major), UK", "Europe/London"),
        ("Paris (Capital), France", "Europe/Paris"),
        ("Berlin (Capital), Germany", "Europe/Berlin"),
        ("Frankfurt (Major), Germany", "Europe/Berlin"),
        ("Munich (Major), Germany", "Europe/Berlin"),
        ("Rome (Capital), Italy", "Europe/Rome"),
        ("Milan (Major), Italy", "Europe/Rome"),
        ("Madrid (Capital), Spain", "Europe/Madrid"),
        ("Barcelona (Major), Spain", "Europe/Madrid"),
        ("Moscow (Capital), Russia", "Europe/Moscow"),
        ("St. Petersburg (Major), Russia", "Europe/Moscow")
    ],
    "Europe (ইউরোপ - ২)": [
        ("Amsterdam (Capital), Netherlands", "Europe/Amsterdam"),
        ("Brussels (Capital), Belgium", "Europe/Brussels"),
        ("Zurich (Major), Switzerland", "Europe/Zurich"),
        ("Geneva (Major), Switzerland", "Europe/Zurich"),
        ("Vienna (Capital), Austria", "Europe/Vienna"),
        ("Stockholm (Capital), Sweden", "Europe/Stockholm"),
        ("Oslo (Capital), Norway", "Europe/Oslo"),
        ("Copenhagen (Capital), Denmark", "Europe/Copenhagen"),
        ("Helsinki (Capital), Finland", "Europe/Helsinki"),
        ("Athens (Capital), Greece", "Europe/Athens"),
        ("Istanbul (Major), Turkey", "Europe/Istanbul"),
        ("Ankara (Capital), Turkey", "Europe/Istanbul"),
        ("Dublin (Capital), Ireland", "Europe/Dublin"),
        ("Lisbon (Capital), Portugal", "Europe/Lisbon")
    ],
    "North America (উত্তর আমেরিকা)": [
        ("Washington DC (Capital), USA", "America/New_York"),
        ("New York (Major), USA", "America/New_York"),
        ("Los Angeles (Major), USA", "America/Los_Angeles"),
        ("Chicago (Major), USA", "America/Chicago"),
        ("Houston (Major), USA", "America/Chicago"),
        ("San Francisco (Major), USA", "America/Los_Angeles"),
        ("Ottawa (Capital), Canada", "America/Toronto"),
        ("Toronto (Major), Canada", "America/Toronto"),
        ("Vancouver (Major), Canada", "America/Vancouver"),
        ("Montreal (Major), Canada", "America/Toronto"),
        ("Mexico City (Capital), Mexico", "America/Mexico_City"),
        ("Havana (Capital), Cuba", "America/Havana")
    ],
    "South America (দক্ষিণ আমেরিকা)": [
        ("Brasilia (Capital), Brazil", "America/Sao_Paulo"),
        ("Sao Paulo (Major), Brazil", "America/Sao_Paulo"),
        ("Rio de Janeiro (Major), Brazil", "America/Sao_Paulo"),
        ("Buenos Aires (Capital), Argentina", "America/Argentina/Buenos_Aires"),
        ("Santiago (Capital), Chile", "America/Santiago"),
        ("Bogota (Capital), Colombia", "America/Bogota"),
        ("Lima (Capital), Peru", "America/Lima"),
        ("Caracas (Capital), Venezuela", "America/Caracas")
    ],
    "Africa (আফ্রিকা)": [
        ("Cairo (Capital), Egypt", "Africa/Cairo"),
        ("Pretoria (Capital), South Africa", "Africa/Johannesburg"),
        ("Johannesburg (Major), South Africa", "Africa/Johannesburg"),
        ("Cape Town (Major), South Africa", "Africa/Johannesburg"),
        ("Nairobi (Capital), Kenya", "Africa/Nairobi"),
        ("Abuja (Capital), Nigeria", "Africa/Lagos"),
        ("Lagos (Major), Nigeria", "Africa/Lagos"),
        ("Rabat (Capital), Morocco", "Africa/Casablanca"),
        ("Casablanca (Major), Morocco", "Africa/Casablanca"),
        ("Addis Ababa (Capital), Ethiopia", "Africa/Addis_Ababa"),
        ("Accra (Capital), Ghana", "Africa/Accra"),
        ("Algiers (Capital), Algeria", "Africa/Algiers")
    ],
    "Oceania (ওশেনিয়া)": [
        ("Canberra (Capital), Australia", "Australia/Sydney"),
        ("Sydney (Major), Australia", "Australia/Sydney"),
        ("Melbourne (Major), Australia", "Australia/Melbourne"),
        ("Brisbane (Major), Australia", "Australia/Brisbane"),
        ("Perth (Major), Australia", "Australia/Perth"),
        ("Wellington (Capital), New Zealand", "Pacific/Auckland"),
        ("Auckland (Major), New Zealand", "Pacific/Auckland"),
        ("Suva (Capital), Fiji", "Pacific/Fiji")
    ]
}

for region, cities in world_cities.items():
    region_menu = tk.Menu(world_clock_menu, tearoff=0)
    for city, tz in cities:
        region_menu.add_command(label=city, command=lambda c=city, t=tz: show_world_time(c, t))
    world_clock_menu.add_cascade(label=region, menu=region_menu)

tools_menu.add_cascade(label="World Clock", menu=world_clock_menu)
menubar.add_cascade(label="Tools", menu=tools_menu)

about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="Developer Info",command=developer_info)
about_menu.add_command(label="Team member info")

menubar.add_cascade(label="About", menu=about_menu)

root.config(menu=menubar)

# --- Main interface UI elements ---
main_frame = tk.Frame(root, bg=current_bg)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

day_label = tk.Label(main_frame, text="", font=(selected_font_family, 15, "bold"), bg=current_bg, fg=current_footer_fg)
day_label.pack(anchor="nw", padx=10)

time_frame = tk.Frame(main_frame, bg=current_bg)
time_frame.pack(pady=5)

time_label = tk.Label(time_frame, text="", font=(selected_font_family, 110, "bold"), bg=current_bg, fg=current_fg)
time_label.pack(side="left")

sec_frame = tk.Frame(time_frame, bg=current_bg)
sec_frame.pack(side="left", padx=15, pady=(45, 0))

sec_label = tk.Label(sec_frame, text="", font=(selected_font_family, 45, "bold"), bg=current_bg, fg=current_sec_fg)
sec_label.pack()

ampm_label = tk.Label(sec_frame, text="", font=(selected_font_family, 22, "bold"), bg=current_bg, fg=current_sec_fg)
ampm_label.pack()

footer_frame = tk.Frame(main_frame, bg=current_bg)
footer_frame.pack(fill="x", padx=10, pady=10)

date_label = tk.Label(footer_frame, text="", font=(selected_font_family, 18), bg=current_bg, fg=current_footer_fg)
date_label.pack(side="left")

battery_label = tk.Label(footer_frame, text="🔋 Checking...", font=("Arial", 12, "bold"), bg=current_bg, fg=current_sec_fg)
battery_label.pack(side="right", padx=10)

tz_label = tk.Label(footer_frame, text="BST", font=("Arial", 12, "bold"), bg=current_bg, fg="#4682b4")
tz_label.pack(side="right", padx=10)

update_time()
root.mainloop()