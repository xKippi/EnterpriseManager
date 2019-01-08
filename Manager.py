#!/usr/bin/env python3
import mysql.connector
import tkinter
import tkinter.messagebox

from calendar import monthrange
from PIL import Image, ImageTk


# Database methods
def add_emp(emp_no, first_name, last_name, gender, birth_date, salary, title, dept_no, db):
    cursor = db.cursor()
    create_emp = "INSERT INTO employees VALUES(%s, %s, %s, %s, %s, NOW())"
    add_salary = "INSERT INTO salaries VALUES(%s, %s, NOW(), '9999-01-01')"
    add_title = "INSERT INTO titles VALUES(%s, %s, NOW(), '9999-01-01')"
    add_dept = "INSERT INTO dept_emp VALUES(%s, %s, NOW(), '9999-01-01')"
    values = (emp_no, birth_date, first_name, last_name, gender)

    cursor.execute(create_emp, values)
    cursor.execute(add_salary, (emp_no, salary))
    cursor.execute(add_title, (emp_no, title))
    cursor.execute(add_dept, (emp_no, dept_no))
    cursor.close()
    db.commit()


def get_emps(db, low=None, high=None):
    cursor = db.cursor()
    # The e.emp_no<~0 statement is important for ordering performance for some reasons...
    stmt = "SELECT e.emp_no, first_name, last_name, gender, birth_date, hire_date, salary, dept_name, title\
                FROM employees e\
                JOIN salaries s ON e.emp_no = s.emp_no\
                JOIN titles t ON e.emp_no = t.emp_no\
                JOIN dept_emp de on e.emp_no = de.emp_no\
                JOIN departments d on de.dept_no = d.dept_no\
            WHERE YEAR(s.to_date)=9999 AND YEAR(t.to_date)=9999 AND YEAR(de.to_date)=9999 AND e.emp_no<~0"
    values = []

    for ent in filter_list:
        stmt += " AND "+ent[0]
        values.append(ent[1])

    stmt += " ORDER BY e.emp_no"

    if low is not None and high is not None:
        stmt += " LIMIT %s,%s"
        values += [low, high-low]

    cursor.execute(stmt, values)
    result = cursor.fetchall()
    return result


def rm_emp(emp_no, db):
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE emp_no=%s", (emp_no,))
    cursor.execute("DELETE FROM salaries WHERE emp_no=%s", (emp_no,))
    cursor.execute("DELETE FROM titles WHERE emp_no=%s", (emp_no,))
    cursor.execute("DELETE FROM dept_emp WHERE emp_no=%s", (emp_no,))
    cursor.close()
    db.commit()

def rm_emp_range(emp_range, db):
    cursor = db.cursor()
    cursor.execute("DELETE FROM employees WHERE emp_no>=%s AND emp_no<=%s", (emp_range['low'], emp_range['high']))
    cursor.execute("DELETE FROM salaries WHERE emp_no>=%s AND emp_no<=%s", (emp_range['low'], emp_range['high']))
    cursor.execute("DELETE FROM titles WHERE emp_no>=%s AND emp_no<=%s", (emp_range['low'], emp_range['high']))
    cursor.execute("DELETE FROM dept_emp WHERE emp_no>=%s AND emp_no<=%s", (emp_range['low'], emp_range['high']))
    cursor.close()
    db.commit()


def change_salary(emp_no, salary, db):
    cursor = db.cursor()
    stmt = "UPDATE salaries SET to_date=NOW() WHERE YEAR(to_date)=9999 AND emp_no = %s"
    cursor.execute(stmt, (emp_no,))

    stmt = "INSERT INTO salaries VALUES(%s, %s, NOW(), '9999-01-01')"
    cursor.execute(stmt, (emp_no, salary))
    cursor.close()
    db.commit()

def change_salary_range(emp_range, salary, db):
    cursor = db.cursor()

    cursor.execute("SELECT emp_no FROM salaries WHERE emp_no>=%s AND emp_no<=%s AND YEAR(to_date)=9999 GROUP BY emp_no",
                   (emp_range['low'], emp_range['high']))

    real_emp_range = cursor.fetchall()

    stmt = "UPDATE salaries SET to_date=NOW() WHERE YEAR(to_date)=9999 AND emp_no>=%s AND emp_no<=%s"
    cursor.execute(stmt, (emp_range['low'], emp_range['high']))

    for emp_no in real_emp_range:
        cursor.execute("INSERT INTO salaries VALUES(%s, %s, NOW(), '9999-01-01')", (emp_no[0], salary))
    cursor.close()
    db.commit()


def get_depts(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM departments ORDER BY dept_no")
    result = cursor.fetchall()

    cursor.close()
    return result


def get_current_year(db):
    cursor = db.cursor()
    cursor.execute("SELECT YEAR(NOW())")
    result = cursor.fetchall()

    cursor.close()
    return result


# GUI and other methods
def open_image(path, width=None, height=None):
    img = Image.open(path)
    orig_width, orig_height = img.size

    if width is None:
        width = orig_width
    if height is None:
        height = orig_height

    img.thumbnail((width, height), Image.ANTIALIAS)
    return ImageTk.PhotoImage(img)


def labeled_entry(master, text, row, entry_bg="snow", entry_width=18, show="", placeholder="", columns=(0, 1), sticky=("W", "E"), padx=(0, 0), pady=(0, 0)):
    tkinter.Label(master, text=text).grid(row=row, column=columns[0], padx=padx, pady=pady)
    entry = tkinter.Entry(master, bg=entry_bg, relief="sunken", width=entry_width, show=show)
    entry.insert(0, placeholder)
    entry.grid(row=row, column=columns[1], sticky=sticky, padx=padx, pady=pady)
    return entry


def day_refresh(day_menu):
    day_menu['menu'].delete(0, 'end')
    days_in_month = monthrange(year_var.get(), month_var.get())[1]
    for i in range(1, days_in_month+1):
        day_menu['menu'].add_command(label=i, command=tkinter._setit(day_var, i))

    if day_var.get() > days_in_month:
        day_var.set(days_in_month)


def date_entry(master, text, row, columns=(0, 1)):
    tkinter.Label(master, text=text).grid(row=row, column=columns[0])
    date_frm = tkinter.Frame(master)
    year = int(get_current_year(dab)[0][0])

    global year_var, month_var, day_var
    year_var = tkinter.IntVar(None, year-67)
    month_var = tkinter.IntVar(None, 1)
    day_var = tkinter.IntVar(None, 1)

    day = tkinter.OptionMenu(date_frm, day_var, 0)
    tkinter.OptionMenu(date_frm, year_var, *range(year-70, year-17), command=lambda val: day_refresh(day)).pack(side="right")
    tkinter.OptionMenu(date_frm, month_var, *range(1, 13), command=lambda val: day_refresh(day)).pack(side="right")

    day_refresh(day)
    day.pack(side="right")

    date_frm.grid(row=row, column=columns[1])
    date_frm.get = lambda: "{}-{}-{}".format(year_var.get(), month_var.get(), day_var.get())
    return date_frm


def is_integer(var):
    try:
        int(var)
        # Calculation should not be parsed as integers
        if '*' in var or '/' in var:
            return False

        if '+' in var[1:] or '-' in var[1:]:
            return False

        return True
    except ValueError:
        return False


def parse_range(var, range_dict):
    if '-' not in var:
        return False

    r = var.split('-')
    try:
        range_dict['low'] = int(r[0])
        range_dict['high'] = int(r[1])
        return True
    except ValueError:
        return False


def update_emp_table():
    global emps, cnt
    emps = get_emps(dab)
    if cnt > len(emps):
        cnt = (len(emps) // EMP_PER_PAGE + 1) * EMP_PER_PAGE

    emp_table(emps, table, next_btn, prev_btn, btm_label, cnt - EMP_PER_PAGE, cnt)


def emp_table(emp_data, table_frame, nxt_btn, prv_btn, btm_lbl, range_low, range_high):
    if range_low < 0:
        raise IndexError("range_low must be at least 0")

    if range_high >= len(emp_data):
        nxt_btn['state'] = "disabled"
        range_high = len(emp_data)
    else:
        nxt_btn['state'] = "normal"

    if range_low <= 0:
        prv_btn['state'] = "disabled"
    else:
        prv_btn['state'] = "normal"

    # Destroy all elements in the table except header
    # You could also just destroy the unnecessary elements and change the text of the slave labels,
    # which would be smoother but leads to a bug in tkinter
    r = 1
    while True:
        column = table_frame.grid_slaves(row=r)
        if len(column) <= 0:
            break
        for cell in column:
            cell.destroy()
        r += 1

    r = 0
    for i in range(range_low, range_high):
        c = 0
        r += 1
        for _d in emp_data[i]:
            tkinter.Label(table_frame, text=_d, width=widths[c], bd=2, anchor="w", relief="sunken", bg="snow").grid(row=r, column=c)
            c += 1

    btm_lbl['text'] = str(range_high) + " of " + str(len(emp_data))


def nxt():
    global cnt
    emp_table(emps, table, next_btn, prev_btn, btm_label, cnt, cnt + EMP_PER_PAGE)
    cnt += EMP_PER_PAGE


def prv():
    global cnt
    cnt -= EMP_PER_PAGE
    emp_table(emps, table, next_btn, prev_btn, btm_label, cnt - EMP_PER_PAGE, cnt)


def check_entry_len(entry, max_len, name="String"):
    if len(entry.get()) > max_len:
        entry['highlightbackground'] = "red"
        tkinter.messagebox.showwarning("Length error", name + " can't be longer than " + str(max_len) + " chars")
        return False
    else:
        entry['highlightbackground'] = default_highlightbackground
        return True


def check_entry_int(entry):
    if is_integer(entry.get()):
        entry['highlightbackground'] = default_highlightbackground
        return True
    else:
        entry['highlightbackground'] = "red"
        return False


def check_entry_int_range(entry, range_dict):
    if is_integer(entry.get()) or parse_range(entry.get(), range_dict):
        entry['highlightbackground'] = default_highlightbackground
        return True
    else:
        entry['highlightbackground'] = "red"
        return False


def add_submit(entries, departments, popup):
    no_error = True
    for i in (0, 5):
        no_error &= check_entry_int(entries[i])

    no_error &= check_entry_len(entries[1], 14, "First name")
    no_error &= check_entry_len(entries[2], 16, "Last name")
    no_error &= check_entry_len(entries[6], 50, "title")

    # Get dept_no of selected department
    for i in departments:
        if dept_var.get() == i[1]:
            entries[7].set(i[0])

    if no_error:
        try:
            add_emp(entries[0].get(), entries[1].get(), entries[2].get(), entries[3].get(),
                    entries[4].get(), entries[5].get(), entries[6].get(), entries[7].get(), dab)
            update_emp_table()
            popup.destroy()
        except mysql.connector.errors.Error as ex:
            tkinter.messagebox.showerror("Error adding employee", "The operation failed with following error: \n" + str(ex))


def rm_submit(entry_emp, popup):
    emp_no = entry_emp.get()
    range_dict = {'low': None, 'high': None}

    if not check_entry_int_range(entry_emp, range_dict):
        tkinter.messagebox.showinfo("Usage", "emp_no must be a single integer or a range of integers!")
        return

    if tkinter.messagebox.askokcancel("Really delete "+str(emp_no)+"?", "Do you really want to delete \""+str(emp_no) +
                                                                        "\"?\nThis action cant be reverted!"):
        try:
            if None in range_dict.values():
                rm_emp(emp_no, dab)
            else:
                rm_emp_range(range_dict, dab)
            update_emp_table()
            popup.destroy()
        except mysql.connector.errors.Error as ex:
            tkinter.messagebox.showerror("Error deleting employee", "The operation failed with following error: \n" + str(ex))


def salary_submit(entries, popup):
    no_error = True
    range_dict = {'low': None, 'high': None}

    no_error &= check_entry_int_range(entries[0], range_dict)
    no_error &= check_entry_int(entries[1])

    if no_error:
        if tkinter.messagebox.askokcancel("Really change salary?", "Do you really want to change the salary of \"{}\" to {}?".format(entries[0].get(), entries[1].get())):
            try:
                if None in range_dict.values():
                    change_salary(entries[0].get(), entries[1].get(), dab)
                else:
                    change_salary_range(range_dict, entries[1].get(), dab)
                update_emp_table()
                popup.destroy()
            except mysql.connector.errors.Error as ex:
                tkinter.messagebox.showerror("Error changing salary", "The operation failed with following error: \n" + str(ex))
    else:
        tkinter.messagebox.showinfo("Usage", "emp_no must be a single integer or a range of integers!\n"
                                             "salary must be a single, positive integer!")


def eval_filter_entry(name, value, radio_value):
    if len(value) > 0:
        if radio_value == 0:
            filter_list.append((name+" LIKE %s", '%{}%'.format(value)))
        else:
            filter_list.append((name+"=%s", value))

def filter_submit(entries, popup):
    global filter_list
    filter_list = []
    range_dict = {}
    if len(entries[0].get()) > 0:
        if is_integer(entries[0].get()):
            entries[0]['highlightbackground'] = default_highlightbackground
            filter_list.append(('e.emp_no=%s', entries[0].get()))
        elif parse_range(entries[0].get(), range_dict):
            entries[0]['highlightbackground'] = default_highlightbackground
            filter_list.append(('e.emp_no>=%s', range_dict['low']))
            filter_list.append(('e.emp_no<=%s', range_dict['high']))
        else:
            entries[0]['highlightbackground'] = "red"
            return

    eval_filter_entry('first_name', entries[1].get(), first_like_var.get())
    eval_filter_entry('last_name', entries[2].get(), last_like_var.get())

    try:
        update_emp_table()
        popup.destroy()
    except mysql.connector.errors.Error as ex:
        tkinter.messagebox.showerror("Error filtering employees", "The operation failed with following error: \n" + str(ex))


def add():
    popup = tkinter.Toplevel(root)
    popup.title("Create employee")
    popup.tk.call('wm', 'iconphoto', popup._w, add_img)
    popup.grab_set()

    frm = tkinter.Frame(popup)
    frm.pack()

    names = ("emp_no", "First name", "Last name", "Gender", "Birth date", "Salary", "Title", "Department")
    entries = []
    global gender_var

    for i in range(0, len(names)):
        if i == 4:
            entries.append(date_entry(frm, names[i]+": ", i))
        else:
            entries.append(labeled_entry(frm, names[i]+": ", i))

    entries[3].destroy()
    entries[7].destroy()

    entries[3] = gender_var = tkinter.StringVar(None, "M")
    radio_frm = tkinter.Frame(frm)
    tkinter.Radiobutton(radio_frm, text="Female", variable=gender_var, value='F').pack(side="right")
    tkinter.Radiobutton(radio_frm, text="Male", variable=gender_var, value='M').pack(side="left")
    radio_frm.grid(row=3, column=1, sticky=("N", "S", "E", "W"))

    dept_names = []
    depts = get_depts(dab)
    for i in depts:
        dept_names.append(i[1])

    global dept_var
    dept_var = tkinter.StringVar(None, dept_names[0])
    entries[7] = tkinter.StringVar()
    tkinter.OptionMenu(frm, dept_var, *dept_names).grid(row=7, column=1, sticky=("N", "S", "E", "W"))

    tkinter.Button(popup, text="Add employee", height=2, command=lambda: add_submit(entries, depts, popup)).pack(pady=(3, 0))


# TODO: Add comma seperated list support
def remove():
    popup = tkinter.Toplevel(root)
    popup.title("Delete employees")
    popup.tk.call('wm', 'iconphoto', popup._w, remove_img)
    popup.grab_set()

    frm = tkinter.Frame(popup)
    frm.pack(pady=(5, 0), padx=10)

    emp_entry = labeled_entry(frm, "emp_no: ", 0)

    tkinter.Button(frm, width=32, height=32, image=delete_img, command=lambda: rm_submit(emp_entry, popup))\
        .grid(row=0, column=2, padx=(10, 0))


def salary_popup():
    popup = tkinter.Toplevel(root)
    popup.title("Change salary")
    popup.tk.call('wm', 'iconphoto', popup._w, salary_img)
    popup.grab_set()

    frm = tkinter.Frame(popup)
    frm.pack(pady=5)

    entries = [labeled_entry(frm, "emp_no: ", 0), labeled_entry(frm, "New salary: ", 1)]

    tkinter.Button(popup, text="Change salary", height=2, command=lambda: salary_submit(entries, popup)).pack()


# TODO: Safe filter options (display them in dialogue)
# TODO: Add all available columns and add order by clause
# TODO: Add filter on/off button
def filter_emp():
    popup = tkinter.Toplevel(root)
    popup.title("Filter employees")
    popup.tk.call('wm', 'iconphoto', popup._w, filter_img)
    popup.grab_set()

    frm = tkinter.Frame(popup)
    frm.pack(pady=5)

    entries = [labeled_entry(frm, "emp_no", 0, columns=(0, 2))]
    tkinter.Label(frm, text="in").grid(row=0, column=1)

    global first_like_var
    first_like_var = tkinter.IntVar(None, 0)
    entries.append(labeled_entry(frm, "First name", 2, columns=(0, 2)))

    radio_frm = tkinter.Frame(frm)
    tkinter.Radiobutton(radio_frm, text="contains", variable=first_like_var, value=0).pack(side="top", anchor="nw")
    tkinter.Radiobutton(radio_frm, text="equals", variable=first_like_var, value=1).pack(side="bottom", anchor="sw")
    radio_frm.grid(row=2, column=1, sticky="W", padx=(0, 5), pady=(10, 2))

    global last_like_var
    last_like_var = tkinter.IntVar(None, 0)
    entries.append(labeled_entry(frm, "Last name", 3, columns=(0, 2)))

    radio_frm = tkinter.Frame(frm)
    tkinter.Radiobutton(radio_frm, text="contains", variable=last_like_var, value=0).pack(side="top", anchor="nw")
    tkinter.Radiobutton(radio_frm, text="equals", variable=last_like_var, value=1).pack(side="bottom", anchor="sw")
    radio_frm.grid(row=3, column=1, sticky="W", padx=(0, 5), pady=(2, 10))

    # entries.append(labeled_entry(frm, "Gender", 4, columns=(0, 2)))
    # tkinter.Label(frm, text="equals").grid(row=4, column=1)

    tkinter.Button(popup, text="Filter", height=2, command=lambda: filter_submit(entries, popup)).pack()


def connect_to_db(entries, success, db_wrapper, emp_wrapper):
    try:
        db_wrapper.append(mysql.connector.connect(
            user=entries[0].get(),
            passwd=entries[1].get(),
            db=entries[2].get(),
            host=entries[3].get(),
            port=entries[4].get()
        ))

        success.set(1)
        emp_wrapper.append(get_emps(db_wrapper[0]))
        root.destroy()
    except mysql.connector.Error as ex:
        tkinter.messagebox.showerror("Error connecting to database", "Connecting to database server failed with following error: \n" + str(ex))


root = tkinter.Tk()
version = "v1.0"
EMP_PER_PAGE = 500
widths = [9, 14, 16, 6, 10, 10, 9, 20, 20]
filter_list = []
default_highlightbackground = tkinter.Entry(None).cget('highlightbackground')

root.title("EnterpriseManager "+version+" - Connect to database")
icon_img = open_image('business.png', 512, 512)
root.tk.call('wm', 'iconphoto', root._w, icon_img)

### LOGIN ###
login_success = tkinter.IntVar(None, False)
dab_wrapper = []
emps_wrapper = []
login_frame = tkinter.Frame(root)
login_frame.pack(padx=10, pady=10)

entry_fields = [labeled_entry(login_frame, "Username: ", 0),
           labeled_entry(login_frame, "Password: ", 1, show='*'),
           labeled_entry(login_frame, "Database: ", 2),
           labeled_entry(login_frame, "Host: ", 3, placeholder="localhost", pady=(10, 0)),
           labeled_entry(login_frame, "Port: ", 4, placeholder="3306")]

tkinter.Button(root, text="Connect", bg="#90EE90", activebackground="#90DD90",
               command=lambda: connect_to_db(entry_fields, login_success, dab_wrapper, emps_wrapper)).pack()
root.mainloop()
### END LOGIN ###

if not login_success.get():
    exit(0)

dab = dab_wrapper[0]
emps = emps_wrapper[0]

root = tkinter.Tk()
root.title("EnterpriseManager "+version)
root.geometry("984x512")
icon_img = open_image('business.png', 512, 512)
root.tk.call('wm', 'iconphoto', root._w, icon_img)

container = tkinter.LabelFrame(root, bg="snow2")
container.pack(fill="x", side="top")

delete_img = open_image("delete.png", 32, 32)
filter_img = open_image("filter.png", 32, 32)
add_img = open_image("addUser.png", 32, 32)
remove_img = open_image("removeUser.png", 32, 32)
salary_img = open_image("salary.png", 24, 24)

tkinter.Button(container, width=32, height=32, image=salary_img, command=salary_popup).pack(side="right")
tkinter.Button(container, width=32, height=32, image=remove_img, command=remove).pack(side="right")
tkinter.Button(container, width=32, height=32, image=add_img, command=add).pack(side="right")
tkinter.Button(container, width=32, height=32, image=filter_img, command=filter_emp).pack(side="left")

container_emp = tkinter.Frame(root, bg="snow")
container_emp.pack(expand=1, fill="both", side="top")

canvas = tkinter.Canvas(container_emp)
canvas_frame = tkinter.Frame(canvas)
table = tkinter.Frame(canvas_frame)
scrollbar = tkinter.Scrollbar(container_emp, orient="vertical", bg="azure2", troughcolor="snow3", command=canvas.yview)
container_nav = tkinter.Frame(root, bg="snow2")

# TODO: Center table and make scrollable
canvas.configure(yscrollcommand=scrollbar.set)
canvas.create_window((0, 0), window=canvas_frame, anchor='nw')
canvas_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

scrollbar.pack(side="right", fill="y")
canvas.pack(fill="both", side="right", expand=1)
table.pack(fill="both", expand=1)
container_nav.pack(side="bottom", fill="x", pady=(3, 0))

cnt = 0
prev_btn = tkinter.Button(container_nav, text="Prev", height=1, width=5, command=prv)
next_btn = tkinter.Button(container_nav, text="Next", height=1, width=5, command=nxt)
btm_label = tkinter.Label(container_nav, bg="snow2")

prev_btn.pack(side="left")
next_btn.pack(side="right")
btm_label.pack(anchor="center", side="bottom")

col = 0
for s in ("emp_no", "first_name", "last_name", "gender", "birth_date", "hire_date", "salary", "dept_name", "title"):
    tkinter.Label(table, text=s, width=widths[col], bd=2, relief="sunken", bg="peach puff").grid(row=0, column=col)
    col += 1

nxt()

root.mainloop()
dab.close()
