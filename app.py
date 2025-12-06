import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

DB_PATH = "erp_ergon.db"

# ------------------------------------------------------------
# ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ
# ------------------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ΠΕΛΑΤΕΣ
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            afm TEXT,
            phone TEXT,
            email TEXT,
            notes TEXT
        )
    """)

    # ΠΡΟΜΗΘΕΥΤΕΣ
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            afm TEXT,
            phone TEXT,
            email TEXT,
            notes TEXT
        )
    """)

    # ΕΡΓΑ
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client_id INTEGER,
            address TEXT,
            status TEXT,
            notes TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)

    # ΚΙΝΗΣΕΙΣ ΠΡΟΜΗΘΕΥΤΩΝ
    c.execute("""
        CREATE TABLE IF NOT EXISTS supplier_tx (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            tx_date TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            tx_type TEXT NOT NULL CHECK(tx_type IN ('invoice','payment')),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    # ΕΞΤΡΑ ΚΟΣΤΗ ΕΡΓΩΝ
    c.execute("""
        CREATE TABLE IF NOT EXISTS project_extra_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            supplier_id INTEGER,
            cost_date TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    # ΕΚΚΡΕΜΟΤΗΤΕΣ ΕΡΓΩΝ
    c.execute("""
        CREATE TABLE IF NOT EXISTS project_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            due_date TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()


def fetch_all(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def execute(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


# ------------------------------------------------------------
# ΠΕΛΑΤΕΣ
# ------------------------------------------------------------
def page_clients():
    st.subheader("Πελάτες")

    with st.form("add_client"):
        name = st.text_input("Επωνυμία *")
        afm = st.text_input("ΑΦΜ")
        phone = st.text_input("Τηλέφωνο")
        email = st.text_input("Email")
        notes = st.text_area("Σημειώσεις")
        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            if not name.strip():
                st.error("Η επωνυμία είναι υποχρεωτική.")
            else:
                execute(
                    "INSERT INTO clients (name, afm, phone, email, notes) VALUES (?,?,?,?,?)",
                    (name, afm, phone, email, notes)
                )
                st.success("Πελάτης καταχωρήθηκε.")

    st.markdown("---")
    rows = fetch_all("SELECT * FROM clients ORDER BY name")

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν πελάτες.")


# ------------------------------------------------------------
# ΠΡΟΜΗΘΕΥΤΕΣ
# ------------------------------------------------------------
def page_suppliers():
    st.subheader("Προμηθευτές")

    with st.form("add_supplier"):
        name = st.text_input("Επωνυμία *")
        afm = st.text_input("ΑΦΜ")
        phone = st.text_input("Τηλέφωνο")
        email = st.text_input("Email")
        notes = st.text_area("Σημειώσεις")
        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            execute(
                "INSERT INTO suppliers (name, afm, phone, email, notes) VALUES (?,?,?,?,?)",
                (name, afm, phone, email, notes)
            )
            st.success("Προμηθευτής προστέθηκε.")

    st.markdown("---")
    rows = fetch_all("SELECT * FROM suppliers ORDER BY name")

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν προμηθευτές.")


# ------------------------------------------------------------
# ΕΡΓΑ
# ------------------------------------------------------------
def page_projects():
    st.subheader("Έργα")

    clients = fetch_all("SELECT id, name FROM clients ORDER BY name")
    client_map = {c["name"]: c["id"] for c in clients}

    with st.form("add_project"):
        name = st.text_input("Όνομα έργου *")
        client = st.selectbox("Πελάτης", ["—"] + list(client_map.keys()))
        address = st.text_input("Διεύθυνση")
        status = st.text_input("Κατάσταση")
        notes = st.text_area("Σημειώσεις")
        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            client_id = None if client == "—" else client_map[client]
            execute(
                "INSERT INTO projects (name, client_id, address, status, notes) VALUES (?,?,?,?,?)",
                (name, client_id, address, status, notes)
            )
            st.success("Έργο καταχωρήθηκε.")

    st.markdown("---")
    rows = fetch_all("""
        SELECT p.id, p.name, c.name AS client, p.address, p.status, p.notes
        FROM projects p
        LEFT JOIN clients c ON p.client_id = c.id
        ORDER BY p.id DESC
    """)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν έργα.")


# ------------------------------------------------------------
# ΕΞΤΡΑ ΚΟΣΤΗ
# ------------------------------------------------------------
def page_extra_costs():
    st.subheader("Έξτρα Κόστη")

    projects = fetch_all("SELECT id, name FROM projects ORDER BY name")
    suppliers = fetch_all("SELECT id, name FROM suppliers ORDER BY name")

    project_map = {p["name"]: p["id"] for p in projects}
    supplier_map = {s["name"]: s["id"] for s in suppliers}

    with st.form("extra_cost_form"):
        project = st.selectbox("Έργο *", list(project_map.keys()))
        supplier = st.selectbox("Προμηθευτής", ["—"] + list(supplier_map.keys()))
        cost_date = st.date_input("Ημερομηνία", value=date.today())
        description = st.text_input("Περιγραφή")
        amount = st.number_input("Ποσό (€)", min_value=0.0)

        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            supplier_id = None if supplier == "—" else supplier_map[supplier]
            execute(
                """
                INSERT INTO project_extra_costs (project_id, supplier_id, cost_date, description, amount)
                VALUES (?,?,?,?,?)
                """,
                (project_map[project], supplier_id, cost_date.isoformat(), description, amount)
            )
            st.success("Έξτρα κόστος καταχωρήθηκε.")

    st.markdown("---")
    rows = fetch_all("""
        SELECT ec.id, p.name AS project, s.name AS supplier, ec.cost_date, ec.description, ec.amount
        FROM project_extra_costs ec
        JOIN projects p ON ec.project_id = p.id
        LEFT JOIN suppliers s ON ec.supplier_id = s.id
        ORDER BY ec.cost_date DESC
    """)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν έξτρα κόστη.")


# ------------------------------------------------------------
# ΕΚΚΡΕΜΟΤΗΤΕΣ ΕΡΓΩΝ
# ------------------------------------------------------------
def page_project_tasks():
    st.subheader("Εκκρεμότητες έργων")

    projects = fetch_all("SELECT id, name FROM projects ORDER BY name")
    project_map = {p["name"]: p["id"] for p in projects}

    with st.form("task_form"):
        project = st.selectbox("Έργο *", list(project_map.keys()))
        title = st.text_input("Τίτλος")
        description = st.text_area("Περιγραφή")
        due_date = st.date_input("Προθεσμία", value=date.today())
        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            execute(
                """
                INSERT INTO project_tasks (project_id, title, description, status, due_date)
                VALUES (?,?,?,?,?)
                """,
                (project_map[project], title, description, "open", due_date.isoformat())
            )
            st.success("Εκκρεμότητα προστέθηκε.")

    st.markdown("---")
    rows = fetch_all("""
        SELECT t.id, p.name AS project, t.title, t.description, t.status, t.due_date
        FROM project_tasks t
        JOIN projects p ON t.project_id = p.id
        ORDER BY t.status ASC, t.due_date ASC
    """)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν εκκρεμότητες.")


# ------------------------------------------------------------
# ΚΙΝΗΣΕΙΣ ΠΡΟΜΗΘΕΥΤΩΝ
# ------------------------------------------------------------
def page_supplier_transactions():
    st.subheader("Κινήσεις προμηθευτών")

    suppliers = fetch_all("SELECT id, name FROM suppliers ORDER BY name")
    supplier_map = {s["name"]: s["id"] for s in suppliers}

    with st.form("supplier_tx_form"):
        supplier = st.selectbox("Προμηθευτής *", list(supplier_map.keys()))
        tx_date = st.date_input("Ημερομηνία", value=date.today())
        description = st.text_input("Περιγραφή")
        amount = st.number_input("Ποσό", min_value=0.0)
        tx_type = st.radio("Τύπος", ["Τιμολόγιο (+)", "Πληρωμή (-)"])

        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            tx = "invoice" if "Τιμολόγιο" in tx_type else "payment"
            execute(
                """
                INSERT INTO supplier_tx (supplier_id, tx_date, description, amount, tx_type)
                VALUES (?,?,?,?,?)
                """,
                (supplier_map[supplier], tx_date.isoformat(), description, amount, tx)
            )
            st.success("Κίνηση καταχωρήθηκε.")

    st.markdown("---")
    rows = fetch_all("""
        SELECT t.id, s.name AS supplier, t.tx_date, t.description, t.amount, t.tx_type
        FROM supplier_tx t
        JOIN suppliers s ON t.supplier_id = s.id
        ORDER BY t.tx_date DESC
    """)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν κινήσεις.")


# ------------------------------------------------------------
# ΑΝΑΦΟΡΕΣ
# ------------------------------------------------------------
def page_reports():
    st.subheader("Υπόλοιπα προμηθευτών")

    rows = fetch_all("""
        SELECT s.name,
               SUM(
                   CASE
                       WHEN t.tx_type = 'invoice' THEN t.amount
                       WHEN t.tx_type = 'payment' THEN -t.amount
                       ELSE 0
                   END
               ) AS balance
        FROM suppliers s
        LEFT JOIN supplier_tx t ON s.id = t.supplier_id
        GROUP BY s.id
        ORDER BY s.name
    """)

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df)
    else:
        st.info("Δεν υπάρχουν δεδομένα.")


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
def page_dashboard():
    st.subheader("Dashboard")

    extra = fetch_all("""
        SELECT p.name, IFNULL(SUM(ec.amount),0) AS total
        FROM projects p
        LEFT JOIN project_extra_costs ec ON p.id = ec.project_id
        GROUP BY p.id
    """)

    tasks = fetch_all("""
        SELECT p.name,
               SUM(CASE WHEN t.status='open' THEN 1 ELSE 0 END) AS open_tasks,
               SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END) AS done_tasks
        FROM projects p
        LEFT JOIN project_tasks t ON p.id = t.project_id
        GROUP BY p.id
    """)

    tmap = {t["name"]: t for t in tasks}

    data = []
    for e in extra:
        t = tmap.get(e["name"], {"open_tasks":0, "done_tasks":0})
        data.append({
            "Έργο": e["name"],
            "Έξτρα Κόστη (€)": e["total"],
            "Ανοιχτές Εκκρεμότητες": t["open_tasks"],
            "Ολοκληρωμένες": t["done_tasks"]
        })

    df = pd.DataFrame(data)
    st.dataframe(df)


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
def main():
    st.set_page_config(page_title="Διαχείριση έργων", layout="wide")
    st.title("Διαχείριση έργων – πελατών – προμηθευτών")

    tabs = st.tabs([
        "Πελάτες",
        "Προμηθευτές",
        "Έργα",
        "Έξτρα Κόστη",
        "Εκκρεμότητες",
        "Κινήσεις Προμηθευτών",
        "Αναφορές",
        "Dashboard"
    ])

    with tabs[0]: page_clients()
    with tabs[1]: page_suppliers()
    with tabs[2]: page_projects()
    with tabs[3]: page_extra_costs()
    with tabs[4]: page_project_tasks()
    with tabs[5]: page_supplier_transactions()
    with tabs[6]: page_reports()
    with tabs[7]: page_dashboard()


init_db()
main()

