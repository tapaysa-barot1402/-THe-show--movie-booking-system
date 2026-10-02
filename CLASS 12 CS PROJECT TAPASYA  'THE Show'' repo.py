# the_show_simple.py
# Simple CBSE-friendly Movie + Restaurant Booking system
# Single-file, procedural, Tkinter + MySQL
# MySQL user: root, password: ihate, database: the_show

import tkinter as tk
from tkinter import messagebox, simpledialog
import mysql.connector
from datetime import datetime

# ------------------ DB CREDENTIALS (you provided) ------------------
DB_USER = "root"
DB_PASS = "ihate"
DB_NAME = "the_show"
DB_HOST = "localhost"
# -------------------------------------------------------------------

# Theme colors
BG = "#2C003E"       # dark purple
LITE = "#7B2CBF"     # light purple
TXT = "#FFFFFF"      # white

# Globals to track logged user
logged_user_id = None
logged_username = None

# ---------------- DB: create DB and tables if not exist ----------------
def connect_mysql(dbname=None):
    try:
        if dbname:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=dbname)
        else:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
        return conn
    except Exception as e:
        messagebox.showerror("Database Error", "Cannot connect to MySQL.\nMake sure MySQL is running.\n\nError: " + str(e))
        return None

def create_database_and_tables():
    # connect without database to create it if needed
    con = connect_mysql()
    if con is None:
        return False
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME)
    con.commit()
    cur.close()
    con.close()

    # connect to the new DB and create tables
    con = connect_mysql(DB_NAME)
    if con is None:
        return False
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) UNIQUE,
        password VARCHAR(120),
        name VARCHAR(120),
        dob DATE,
        phone VARCHAR(30),
        email VARCHAR(120),
        address TEXT,
        profile_created TINYINT(1) DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(80) UNIQUE,
        password VARCHAR(120)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(200),
        mood VARCHAR(50),
        duration VARCHAR(30),
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shows (
        id INT AUTO_INCREMENT PRIMARY KEY,
        movie_id INT,
        show_time VARCHAR(80),
        ac TINYINT(1) DEFAULT 1,
        front_seats INT DEFAULT 20,
        middle_seats INT DEFAULT 30,
        back_seats INT DEFAULT 30,
        normal_seats INT DEFAULT 50,
        vip_seats INT DEFAULT 10,
        vvip_seats INT DEFAULT 5,
        kids_seats INT DEFAULT 10,
        couple_seats INT DEFAULT 10,
        senior_seats INT DEFAULT 10
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS restaurant (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(200),
        category VARCHAR(50), -- 'snacks' or 'main'
        price FLOAT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        show_id INT,
        seats_info TEXT,
        pref_ac TINYINT(1),
        pref_location VARCHAR(50),
        food_info TEXT,
        total_amount FLOAT,
        gst FLOAT,
        final_amount FLOAT,
        booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        movie_id INT
    )
    """)

    # default admin if none
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admins (username, password) VALUES (%s,%s)", ("admin", "admin123"))
    con.commit()
    cur.close()
    con.close()
    return True

# ------------------ Simple DB helpers ------------------
def db_query(query, params=(), fetch=False):
    con = connect_mysql(DB_NAME)
    if con is None:
        return None
    cur = con.cursor()
    try:
        cur.execute(query, params)
        if fetch:
            rows = cur.fetchall()
            cur.close()
            con.close()
            return rows
        else:
            con.commit()
            cur.close()
            con.close()
            return True
    except Exception as e:
        cur.close()
        con.close()
        messagebox.showerror("DB Error", str(e))
        return None

# ------------------ GUI: root and frame swap ------------------
root = tk.Tk()
root.title("THe show - Simple Project")
root.geometry("980x650")
root.configure(bg=BG)

current_frame = None

def show_frame(frame):
    global current_frame
    if current_frame:
        current_frame.destroy()
    current_frame = frame
    current_frame.pack(fill="both", expand=True)

# ------------------ Login / Signup screens ------------------
def main_screen():
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="THe show", bg=BG, fg=TXT, font=("Arial", 28, "bold")).pack(pady=20)

    # login fields
    tk.Label(frame, text="Username:", bg=BG, fg=TXT).pack()
    user_e = tk.Entry(frame, width=30)
    user_e.pack(pady=6)
    tk.Label(frame, text="Password:", bg=BG, fg=TXT).pack()
    pass_e = tk.Entry(frame, show="*", width=30)
    pass_e.pack(pady=6)

    # user/admin selector simple checkbox
    login_for = tk.StringVar(value="user")
    tk.Radiobutton(frame, text="User", variable=login_for, value="user", bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=10, pady=10)
    tk.Radiobutton(frame, text="Admin", variable=login_for, value="admin", bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=10, pady=10)

    def do_login():
        username = user_e.get().strip()
        password = pass_e.get().strip()
        if username == "" or password == "":
            messagebox.showwarning("Input needed", "Please enter username and password.")
            return
        if login_for.get() == "user":
            rows = db_query("SELECT id,password,profile_created FROM users WHERE username=%s", (username,), fetch=True)
            if not rows:
                messagebox.showerror("Login failed", "No such user. Please signup first.")
                return
            uid, realpass, prof = rows[0]
            if password != realpass:
                messagebox.showerror("Login failed", "Wrong password.")
                return
            # success
            global logged_user_id, logged_username
            logged_user_id = uid
            logged_username = username
            # if profile not created -> profile screen else user home
            if prof == 0:
                user_profile_screen()
            else:
                user_home_screen()
        else:
            rows = db_query("SELECT id,password FROM admins WHERE username=%s", (username,), fetch=True)
            if not rows:
                messagebox.showerror("Admin Login failed", "No such admin.")
                return
            aid, realpass = rows[0]
            if password != realpass:
                messagebox.showerror("Admin Login failed", "Wrong password.")
                return
            # admin success
            admin_panel()

    def go_signup():
        signup_screen()

    tk.Button(frame, text="Login", command=do_login, bg=LITE, fg=TXT, width=12).pack(pady=12)
    tk.Button(frame, text="Signup (User)", command=go_signup, bg=TXT, fg=BG, width=12).pack()
    tk.Label(frame, text="(Default admin: admin / admin123)", bg=BG, fg=TXT, font=("Arial", 9, "italic")).pack(pady=8)
    show_frame(frame)

def signup_screen():
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="Signup - Create Username & Password", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)

    tk.Label(frame, text="Choose Username:", bg=BG, fg=TXT).pack()
    su = tk.Entry(frame, width=30)
    su.pack(pady=6)
    tk.Label(frame, text="Choose Password:", bg=BG, fg=TXT).pack()
    sp = tk.Entry(frame, show="*", width=30)
    sp.pack(pady=6)

    def do_signup():
        username = su.get().strip()
        password = sp.get().strip()
        if username == "" or password == "":
            messagebox.showwarning("Input needed", "Please enter username and password.")
            return
        # insert
        res = db_query("INSERT INTO users (username,password) VALUES (%s,%s)", (username, password))
        if res is True:
            messagebox.showinfo("Signed up!", "Signup successful. Please login now.")
            main_screen()
        else:
            # likely duplicate
            messagebox.showerror("Error", "Could not create user. Maybe username already exists.")

    tk.Button(frame, text="Create Account", command=do_signup, bg=LITE, fg=TXT, width=14).pack(pady=12)
    tk.Button(frame, text="Back to Login", command=main_screen, bg=TXT, fg=BG, width=14).pack()
    show_frame(frame)

# ------------------ User Profile (one-time) ------------------
def user_profile_screen():
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="Complete Your Profile", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)

    tk.Label(frame, text="Full Name:", bg=BG, fg=TXT).pack()
    name_e = tk.Entry(frame, width=40)
    name_e.pack(pady=4)
    tk.Label(frame, text="DOB (YYYY-MM-DD):", bg=BG, fg=TXT).pack()
    dob_e = tk.Entry(frame, width=20)
    dob_e.pack(pady=4)
    tk.Label(frame, text="Phone:", bg=BG, fg=TXT).pack()
    phone_e = tk.Entry(frame, width=20)
    phone_e.pack(pady=4)
    tk.Label(frame, text="Email (optional):", bg=BG, fg=TXT).pack()
    email_e = tk.Entry(frame, width=40)
    email_e.pack(pady=4)
    tk.Label(frame, text="Address:", bg=BG, fg=TXT).pack()
    addr_e = tk.Text(frame, height=4, width=50)
    addr_e.pack(pady=6)

    def save_profile():
        name = name_e.get().strip()
        dob = dob_e.get().strip()
        phone = phone_e.get().strip()
        email = email_e.get().strip()
        addr = addr_e.get("1.0", "end").strip()
        if name == "" or dob == "" or phone == "":
            messagebox.showwarning("Input needed", "Please fill name, dob, phone.")
            return
        # update
        q = "UPDATE users SET name=%s, dob=%s, phone=%s, email=%s, address=%s, profile_created=1 WHERE id=%s"
        ok = db_query(q, (name, dob, phone, email, addr, logged_user_id))
        if ok:
            messagebox.showinfo("Saved", "Profile saved. Enjoy booking.")
            user_home_screen()
        else:
            messagebox.showerror("Error", "Could not save profile.")

    tk.Button(frame, text="Save Profile", command=save_profile, bg=LITE, fg=TXT, width=14).pack(pady=8)
    show_frame(frame)

# ------------------ User Home: movies, restaurant, wishlist, bookings ------------------
def user_home_screen():
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text=f"Welcome {logged_username}", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)

    # buttons for features
    btn_frame = tk.Frame(frame, bg=BG)
    btn_frame.pack(pady=8)
    tk.Button(btn_frame, text="Browse Movies", width=18, command=browse_movies, bg=LITE, fg=TXT).grid(row=0, column=0, padx=6, pady=6)
    tk.Button(btn_frame, text="Mood-based Movies", width=18, command=mood_movies, bg=LITE, fg=TXT).grid(row=0, column=1, padx=6, pady=6)
    tk.Button(btn_frame, text="Restaurant Menu", width=18, command=restaurant_screen, bg=LITE, fg=TXT).grid(row=0, column=2, padx=6, pady=6)
    tk.Button(btn_frame, text="My Watchlist", width=18, command=watchlist_screen, bg=LITE, fg=TXT).grid(row=1, column=0, padx=6, pady=6)
    tk.Button(btn_frame, text="My Bookings", width=18, command=my_bookings_screen, bg=LITE, fg=TXT).grid(row=1, column=1, padx=6, pady=6)
    tk.Button(btn_frame, text="Logout", width=18, command=logout, bg=TXT, fg=BG).grid(row=1, column=2, padx=6, pady=6)

    show_frame(frame)

def logout():
    global logged_user_id, logged_username
    logged_user_id = None
    logged_username = None
    main_screen()

# ------------------ Browse Movies (normal) ------------------
def browse_movies():
    rows = db_query("SELECT id,title,mood,duration,description FROM movies", fetch=True)
    if rows is None:
        return
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="Movies - Browse", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)
    listbox = tk.Listbox(frame, width=80, height=12)
    listbox.pack(pady=6)
    for r in rows:
        listbox.insert("end", f"{r[0]} - {r[1]} ({r[2]}) - {r[3]}")
    def open_movie():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Select", "Please select a movie.")
            return
        idx = listbox.get(sel[0]).split(" - ")[0]
        movie_detail_screen(int(idx))
    tk.Button(frame, text="Open Movie", command=open_movie, bg=LITE, fg=TXT).pack(pady=6)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack()
    show_frame(frame)

# ------------------ Mood-based Movies ------------------
def mood_movies():
    mood = simpledialog.askstring("Mood", "Enter mood (e.g., romantic, action, funny, family):")
    if not mood:
        return
    rows = db_query("SELECT id,title,mood,duration FROM movies WHERE mood LIKE %s", ("%"+mood+"%",), fetch=True)
    if rows is None:
        return
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text=f"Movies for mood: {mood}", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)
    lb = tk.Listbox(frame, width=80, height=12)
    lb.pack(pady=6)
    for r in rows:
        lb.insert("end", f"{r[0]} - {r[1]} ({r[2]})")
    def openm():
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Select", "Please select a movie.")
            return
        idx = int(lb.get(sel[0]).split(" - ")[0])
        movie_detail_screen(idx)
    tk.Button(frame, text="Open Movie", command=openm, bg=LITE, fg=TXT).pack(pady=6)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack()
    show_frame(frame)

# ------------------ Movie Detail & showtimes ------------------
def movie_detail_screen(movie_id):
    rows = db_query("SELECT id,title,mood,duration,description FROM movies WHERE id=%s", (movie_id,), fetch=True)
    if not rows:
        messagebox.showerror("Error", "Movie not found.")
        return
    m = rows[0]
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text=f"{m[1]}", bg=BG, fg=TXT, font=("Arial", 20, "bold")).pack(pady=6)
    tk.Label(frame, text=f"Mood: {m[2]}    Duration: {m[3]}", bg=BG, fg=TXT).pack()
    tk.Label(frame, text="Description:", bg=BG, fg=TXT).pack(pady=4)
    tk.Label(frame, text=m[4] or "-", bg=BG, fg=TXT, wraplength=900, justify="left").pack(pady=4)

    # shows for this movie
    shows = db_query("SELECT id,show_time,ac,front_seats,middle_seats,back_seats,normal_seats,vip_seats,vvip_seats FROM shows WHERE movie_id=%s", (movie_id,), fetch=True)
    if shows is None:
        return
    lb = tk.Listbox(frame, width=90, height=8)
    lb.pack(pady=6)
    for s in shows:
        lb.insert("end", f"{s[0]} - {s[1]} - AC:{'Yes' if s[2]==1 else 'No'} - Normal:{s[6]} VIP:{s[7]} VVIP:{s[8]}")
    def book_show():
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Select show", "Please select a show/time.")
            return
        sid = int(lb.get(sel[0]).split(" - ")[0])
        seat_selection_screen(sid)
    def add_watchlist():
        # add movie to watchlist
        db_query("INSERT INTO watchlist (user_id,movie_id) VALUES (%s,%s)", (logged_user_id, movie_id))
        messagebox.showinfo("Added", "Movie added to your watchlist.")
    tk.Button(frame, text="Add to Watchlist", command=add_watchlist, bg=LITE, fg=TXT).pack(pady=4)
    tk.Button(frame, text="Book Selected Show", command=book_show, bg=LITE, fg=TXT).pack(pady=6)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack(pady=6)
    show_frame(frame)

# ------------------ Seat selection and food selection, then bill popup ------------------
def seat_selection_screen(show_id):
    # fetch show info
    rows = db_query("SELECT id,show_time,ac,front_seats,middle_seats,back_seats,normal_seats,vip_seats,vvip_seats,kids_seats,couple_seats,senior_seats FROM shows WHERE id=%s", (show_id,), fetch=True)
    if not rows:
        messagebox.showerror("Error", "Show not found.")
        return
    s = rows[0]
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text=f"Show: {s[1]}", bg=BG, fg=TXT, font=("Arial", 16)).pack(pady=8)
    # show available seats simple labels and entry for how many
    seat_vars = {}
    seat_types = [("Normal",6),("VIP",7),("VVIP",8),("Kids",9),("Couple",10),("Senior",11)]
    for st, idx in seat_types:
        avail = s[idx] if idx < len(s) else 0
        rowf = tk.Frame(frame, bg=BG)
        rowf.pack(pady=4)
        tk.Label(rowf, text=f"{st} (available: {avail})", bg=BG, fg=TXT, width=25).pack(side="left")
        ent = tk.Entry(rowf, width=8)
        ent.pack(side="left", padx=8)
        seat_vars[st] = (ent, avail)

    # preferences
    pref_ac = tk.IntVar(value=s[2])
    tk.Label(frame, text="AC Preference:", bg=BG, fg=TXT).pack(pady=4)
    tk.Radiobutton(frame, text="AC", variable=pref_ac, value=1, bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=6)
    tk.Radiobutton(frame, text="Non-AC", variable=pref_ac, value=0, bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=6)

    pref_loc = tk.StringVar(value="middle")
    tk.Label(frame, text="Location Preference:", bg=BG, fg=TXT).pack(pady=6)
    tk.Radiobutton(frame, text="Front", variable=pref_loc, value="front", bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=6)
    tk.Radiobutton(frame, text="Middle", variable=pref_loc, value="middle", bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=6)
    tk.Radiobutton(frame, text="Back", variable=pref_loc, value="back", bg=BG, fg=TXT, selectcolor=BG).pack(side="left", padx=6)

    # food ordering - show simple menu and allow quantities
    food_rows = db_query("SELECT id,name,category,price FROM restaurant", fetch=True)
    food_vars = {}
    if food_rows is None:
        return
    tk.Label(frame, text="Restaurant - add to order (enter qty):", bg=BG, fg=TXT).pack(pady=8)
    for fr in food_rows:
        fid, fname, cat, price = fr
        ff = tk.Frame(frame, bg=BG)
        ff.pack(pady=2, anchor="w")
        tk.Label(ff, text=f"{fname} [{cat}] - ₹{price}", bg=BG, fg=TXT, width=40, anchor="w").pack(side="left")
        fe = tk.Entry(ff, width=6)
        fe.pack(side="left", padx=6)
        food_vars[fid] = (fe, fname, price)

    def finalize_booking():
        # read seat quantities
        seats_chosen = {}
        total = 0.0
        seat_prices = {"Normal":150, "VIP":250, "VVIP":400, "Kids":80, "Couple":300, "Senior":120}
        for st, (ent, avail) in seat_vars.items():
            txt = ent.get().strip()
            if txt == "":
                cnt = 0
            else:
                try:
                    cnt = int(txt)
                except:
                    messagebox.showwarning("Invalid", "Enter numeric seat counts.")
                    return
            if cnt < 0 or cnt > avail:
                messagebox.showwarning("Invalid", f"Invalid count for {st}. Available: {avail}.")
                return
            if cnt > 0:
                seats_chosen[st] = cnt
                total += seat_prices.get(st, 100) * cnt

        # food totals
        food_order = {}
        for fid, (ent, fname, price) in food_vars.items():
            txt = ent.get().strip()
            if txt == "":
                cnt = 0
            else:
                try:
                    cnt = int(txt)
                except:
                    messagebox.showwarning("Invalid", "Enter numeric food counts.")
                    return
            if cnt < 0:
                messagebox.showwarning("Invalid", "Invalid food count.")
                return
            if cnt > 0:
                food_order[fname] = cnt
                total += price * cnt

        if total == 0:
            messagebox.showwarning("No selection", "Choose at least one seat or food item.")
            return

        gst = round(total * 0.18, 2)  # 18% GST
        final = round(total + gst, 2)

        # create seats_info and food_info strings
        seats_info = ",".join([f"{k}:{v}" for k,v in seats_chosen.items()]) if seats_chosen else ""
        food_info = ",".join([f"{k}:{v}" for k,v in food_order.items()]) if food_order else ""

        # insert booking
        ok = db_query("INSERT INTO bookings (user_id,show_id,seats_info,pref_ac,pref_location,food_info,total_amount,gst,final_amount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                      (logged_user_id, show_id, seats_info, pref_ac.get(), pref_loc.get(), food_info, total, gst, final))
        if not ok:
            messagebox.showerror("Error", "Could not save booking.")
            return

        # reduce seat counts in shows table - simple update; subtract from matching columns
        # caution: do sequential updates for types selected
        if seats_chosen:
            for st, cnt in seats_chosen.items():
                col = None
                if st == "Normal":
                    col = "normal_seats"
                elif st == "VIP":
                    col = "vip_seats"
                elif st == "VVIP":
                    col = "vvip_seats"
                elif st == "Kids":
                    col = "kids_seats"
                elif st == "Couple":
                    col = "couple_seats"
                elif st == "Senior":
                    col = "senior_seats"
                if col:
                    db_query(f"UPDATE shows SET {col} = {col} - %s WHERE id=%s", (cnt, show_id))

        # show bill popup
        bill_text = "----- BILL -----\n"
        bill_text += f"User: {logged_username}\n"
        bill_text += f"Show: {s[1]}\n"
        bill_text += f"Seats: {seats_info}\n"
        bill_text += f"Food: {food_info}\n"
        bill_text += f"Subtotal: ₹{total:.2f}\n"
        bill_text += f"GST (18%): ₹{gst:.2f}\n"
        bill_text += f"Total: ₹{final:.2f}\n"
        messagebox.showinfo("Bill (popup only)", bill_text)
        user_home_screen()

    tk.Button(frame, text="Confirm & Pay (Popup Bill)", command=finalize_booking, bg=LITE, fg=TXT).pack(pady=8)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack(pady=6)
    show_frame(frame)

# ------------------ Restaurant screen (view-only + quick add during booking) ------------------
def restaurant_screen():
    rows = db_query("SELECT id,name,category,price FROM restaurant", fetch=True)
    if rows is None:
        return
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="Restaurant Menu", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)
    for r in rows:
        tk.Label(frame, text=f"{r[1]} [{r[2]}] - ₹{r[3]}", bg=BG, fg=TXT, anchor="w").pack(fill="x", padx=20)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack(pady=10)
    show_frame(frame)

# ------------------ Watchlist screen ------------------
def watchlist_screen():
    rows = db_query("SELECT w.id,m.title FROM watchlist w JOIN movies m ON w.movie_id=m.id WHERE w.user_id=%s", (logged_user_id,), fetch=True)
    if rows is None:
        return
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="My Watchlist", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)
    lb = tk.Listbox(frame, width=70)
    lb.pack(pady=6)
    for r in rows:
        lb.insert("end", f"{r[0]} - {r[1]}")
    def remove_item():
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select item to remove.")
            return
        wid = int(lb.get(sel[0]).split(" - ")[0])
        db_query("DELETE FROM watchlist WHERE id=%s", (wid,))
        messagebox.showinfo("Removed", "Removed from watchlist.")
        watchlist_screen()
    tk.Button(frame, text="Remove Selected", command=remove_item, bg=LITE, fg=TXT).pack(pady=6)
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack()
    show_frame(frame)

# ------------------ My Bookings screen ------------------
def my_bookings_screen():
    rows = db_query("SELECT id,show_id,seats_info,food_info,final_amount,booking_time FROM bookings WHERE user_id=%s ORDER BY booking_time DESC", (logged_user_id,), fetch=True)
    if rows is None:
        return
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="My Bookings", bg=BG, fg=TXT, font=("Arial", 18)).pack(pady=10)
    lb = tk.Listbox(frame, width=100)
    lb.pack(pady=6)
    for r in rows:
        lb.insert("end", f"{r[0]} | Show:{r[1]} | Seats:{r[2]} | Food:{r[3]} | Total:₹{r[4]} | {r[5]}")
    tk.Button(frame, text="Back", command=user_home_screen, bg=TXT, fg=BG).pack(pady=8)
    show_frame(frame)

# ------------------ Admin panel (simple) ------------------
def admin_panel():
    frame = tk.Frame(root, bg=BG)
    tk.Label(frame, text="Admin Panel", bg=BG, fg=TXT, font=("Arial", 20)).pack(pady=10)

    def view_bookings():
        rows = db_query("SELECT b.id,u.username,b.show_id,b.seats_info,b.food_info,b.final_amount,b.booking_time FROM bookings b JOIN users u ON b.user_id=u.id ORDER BY b.booking_time DESC", fetch=True)
        if rows is None:
            return
        f2 = tk.Frame(root, bg=BG)
        tk.Label(f2, text="All Bookings", bg=BG, fg=TXT, font=("Arial", 16)).pack(pady=6)
        lb = tk.Listbox(f2, width=110)
        lb.pack(pady=6)
        for r in rows:
            lb.insert("end", f"{r[0]} | user:{r[1]} | show:{r[2]} | seats:{r[3]} | food:{r[4]} | total:₹{r[5]} | {r[6]}")
        tk.Button(f2, text="Back", command=admin_panel, bg=TXT, fg=BG).pack(pady=6)
        show_frame(f2)

    def manage_movies():
        # list movies and options to add/delete
        rows = db_query("SELECT id,title,mood,duration FROM movies", fetch=True)
        if rows is None:
            return
        f2 = tk.Frame(root, bg=BG)
        tk.Label(f2, text="Manage Movies", bg=BG, fg=TXT, font=("Arial", 16)).pack(pady=6)
        lb = tk.Listbox(f2, width=90)
        lb.pack()
        for r in rows:
            lb.insert("end", f"{r[0]} - {r[1]} ({r[2]}) - {r[3]}")
        def add_movie():
            title = simpledialog.askstring("Title", "Movie title:")
            if not title: return
            mood = simpledialog.askstring("Mood", "Mood tag:")
            dur = simpledialog.askstring("Duration", "Duration e.g., 2h 10m:")
            desc = simpledialog.askstring("Description", "Short description:")
            db_query("INSERT INTO movies (title,mood,duration,description) VALUES (%s,%s,%s,%s)", (title,mood,dur,desc))
            manage_movies()
        def delete_movie():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Select", "Select movie to delete.")
                return
            mid = int(lb.get(sel[0]).split(" - ")[0])
            db_query("DELETE FROM movies WHERE id=%s", (mid,))
            manage_movies()
        def add_show_for_movie():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Select", "Select movie to add show for.")
                return
            mid = int(lb.get(sel[0]).split(" - ")[0])
            showt = simpledialog.askstring("Show time", "e.g., 2025-11-01 18:30")
            if not showt: return
            ac = simpledialog.askstring("AC", "AC? (yes/no) default yes").lower() if True else "yes"
            acv = 1 if ac.startswith("y") else 0
            db_query("INSERT INTO shows (movie_id,show_time,ac) VALUES (%s,%s,%s)", (mid, showt, acv))
            messagebox.showinfo("Done", "Show added.")
        tk.Button(f2, text="Add Movie", command=add_movie, bg=LITE, fg=TXT).pack(pady=4)
        tk.Button(f2, text="Delete Selected Movie", command=delete_movie, bg=LITE, fg=TXT).pack(pady=4)
        tk.Button(f2, text="Add Show for Selected Movie", command=add_show_for_movie, bg=LITE, fg=TXT).pack(pady=4)
        tk.Button(f2, text="Back", command=admin_panel, bg=TXT, fg=BG).pack(pady=6)
        show_frame(f2)

    def manage_restaurant():
        rows = db_query("SELECT id,name,category,price FROM restaurant", fetch=True)
        if rows is None:
            return
        f2 = tk.Frame(root, bg=BG)
        tk.Label(f2, text="Manage Restaurant Items", bg=BG, fg=TXT, font=("Arial", 16)).pack(pady=6)
        lb = tk.Listbox(f2, width=90)
        lb.pack()
        for r in rows:
            lb.insert("end", f"{r[0]} - {r[1]} [{r[2]}] - ₹{r[3]}")
        def add_item():
            name = simpledialog.askstring("Name", "Item name:")
            if not name: return
            cat = simpledialog.askstring("Category", "snacks or main:")
            price = simpledialog.askfloat("Price", "Price:")
            db_query("INSERT INTO restaurant (name,category,price) VALUES (%s,%s,%s)", (name,cat,price))
            manage_restaurant()
        def delete_item():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("Select", "Select item to delete.")
                return
            iid = int(lb.get(sel[0]).split(" - ")[0])
            db_query("DELETE FROM restaurant WHERE id=%s", (iid,))
            manage_restaurant()
        tk.Button(f2, text="Add Item", command=add_item, bg=LITE, fg=TXT).pack(pady=4)
        tk.Button(f2, text="Delete Selected Item", command=delete_item, bg=LITE, fg=TXT).pack(pady=4)
        tk.Button(f2, text="Back", command=admin_panel, bg=TXT, fg=BG).pack(pady=6)
        show_frame(f2)

    tk.Button(frame, text="View All Bookings", command=view_bookings, bg=LITE, fg=TXT, width=20).pack(pady=6)
    tk.Button(frame, text="Manage Movies & Shows", command=manage_movies, bg=LITE, fg=TXT, width=20).pack(pady=6)
    tk.Button(frame, text="Manage Restaurant Menu", command=manage_restaurant, bg=LITE, fg=TXT, width=20).pack(pady=6)
    tk.Button(frame, text="Back to Login", command=main_screen, bg=TXT, fg=BG, width=20).pack(pady=12)

    show_frame(frame)

# ------------------ Start app: ensure DB, add some sample data if empty ------------------
ok = create_database_and_tables()
if not ok:
    # DB error already shown
    root.destroy()
else:
    # add some sample movies and food if tables empty (simple)
    if db_query("SELECT COUNT(*) FROM movies", fetch=True)[0][0] == 0:
        db_query("INSERT INTO movies (title,mood,duration,description) VALUES (%s,%s,%s,%s)",
                 ("Starlit Dreams", "romantic", "2h 5m", "A soft romantic film about choices and memories."))
        db_query("INSERT INTO movies (title,mood,duration,description) VALUES (%s,%s,%s,%s)",
                 ("Action Rush", "action", "2h 15m", "Fast-paced action with stunts and thrills."))
        db_query("INSERT INTO movies (title,mood,duration,description) VALUES (%s,%s,%s,%s)",
                 ("Family Fun", "family", "1h 45m", "A family movie perfect for weekend togetherness."))
    if db_query("SELECT COUNT(*) FROM shows", fetch=True)[0][0] == 0:
        # attach basic shows for movie ids 1..3
        db_query("INSERT INTO shows (movie_id,show_time,ac) VALUES (%s,%s,%s)", (1, "2025-11-10 18:30", 1))
        db_query("INSERT INTO shows (movie_id,show_time,ac) VALUES (%s,%s,%s)", (2, "2025-11-10 20:30", 1))
        db_query("INSERT INTO shows (movie_id,show_time,ac) VALUES (%s,%s,%s)", (3, "2025-11-11 17:00", 1))
    if db_query("SELECT COUNT(*) FROM restaurant", fetch=True)[0][0] == 0:
        db_query("INSERT INTO restaurant (name,category,price) VALUES (%s,%s,%s)", ("Popcorn", "snacks", 80.0))
        db_query("INSERT INTO restaurant (name,category,price) VALUES (%s,%s,%s)", ("Cold Drink", "snacks", 50.0))
        db_query("INSERT INTO restaurant (name,category,price) VALUES (%s,%s,%s)", ("Veg Burger", "main", 120.0))
        db_query("INSERT INTO restaurant (name,category,price) VALUES (%s,%s,%s)", ("Paneer Wrap", "main", 150.0))

    main_screen()
    root.mainloop()
