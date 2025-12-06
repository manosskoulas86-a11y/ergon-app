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

    # ΕΡΓΟΔΟΤΕΣ / ΠΕΛΑΤΕΣ (από φύλλο "Εργοδότες")
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,          -- Επωνυμία
            last_name TEXT,             -- Επίθετο
            first_name TEXT,            -- Όνομα
            entity_type TEXT,           -- Σύσταση
            address TEXT,
            postal_code TEXT,
            city TEXT,
            phone_landline TEXT,        -- σταθερό
            phone_mobile TEXT,          -- κινητό
            email TEXT,
            afm TEXT,
            dou TEXT,
            taxis_username TEXT,
            taxis_password TEXT,
            job TEXT                    -- Επάγγελμα
        )
    """)

    # ΠΡΟΜΗΘΕΥΤΕΣ (από φύλλο "Προμηθευτές")
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,          -- Επωνυμία Εταιρίας
            last_name TEXT,
            first_name TEXT,
            entity_type TEXT,           -- Σύσταση
            job TEXT,                   -- Επάγγελμα
            iban1 TEXT,
            bank1 TEXT,
            iban2 TEXT,
            bank2 TEXT,
            iban3 TEXT,
            bank3 TEXT,
            iban4 TEXT,
            bank4 TEXT,
            address TEXT,
            postal_code TEXT,
            city TEXT,
            phone1 TEXT,
            phone2 TEXT,
            email TEXT,
            afm TEXT,
            dou TEXT
        )
    """)

    # ΕΡΓΑ (από φύλλο "Έργα")
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,                      -- Κωδικός Έργου
            reg_date TEXT,                  -- Ημ/νια Εγγραφής
            protocol_no TEXT,               -- αρ. πρωτ
            client_id INTEGER,              -- σχέση με clients
            employer_name TEXT,             -- Εργοδότης (ελεύθερο κείμενο)
            hf_flag TEXT,                   -- ΗΦ-Φ
            project_type TEXT,              -- Είδος Έργου
            priority TEXT,                  -- Προτεραιότητα
            status TEXT,                    -- Κατάσταση
            status2 TEXT,                   -- Κατάσταση2
            description TEXT,               -- Περιγραφή
            address TEXT,                   -- Διεύθυνση εργου
            postal_code TEXT,               -- ΤΚ
            city TEXT,                      -- Πόλη
            agreed_amount REAL,             -- Συμφωνημένη Αξία
            invoice_expenses REAL,          -- Έξοδα παραστατικα
            engineer TEXT,                  -- Μηχανικός
            apy TEXT,                       -- ΑΠΥ
            manager TEXT,                   -- Μάνος-Θανάσης
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)

    # ΠΑΡΑΣΤΑΤΙΚΑ (από φύλλο "Παραστατικά")
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seq_no INTEGER,                 -- α/α
            doc_date TEXT,                  -- Ημ/νία Παρ/τικού
            project_id INTEGER,             -- Έργα (σχέση με projects)
            billing_type TEXT,              -- Τιμολόγηση
            supplier_id INTEGER,            -- Προμηθευτής - Συνεργείο
            work_title TEXT,                -- Εργασία
            description TEXT,               -- Περιγραφή
            charge REAL,                    -- Χρέωση
            vat REAL,                       -- ΦΠΑ
            credit REAL,                    -- Πίστωση
            payment_method TEXT,            -- Τρόπος Πληρωμής
            payments REAL,                  -- Καταβολές
            payment_target TEXT,            -- Που καταβληθηκαν
            day TEXT,                       -- ΗΜΕΡΑ (κείμενο/αριθμός)
            month TEXT,                     -- ΜΗΝΑ
            year TEXT,                      -- ΕΤΟΣ
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    # ΗΜΕΡΟΛΟΓΙΟ (από φύλλο "Ημερολόγιο")
    c.execute("""
        CREATE TABLE IF NOT EXISTS worklog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,                  -- Ημερομηνία
            employee TEXT,                  -- Υπάλληλος
            project_id INTEGER,             -- Έργο (σχέση με projects)
            work_desc TEXT,                 -- Εργασία
            hours REAL,                     -- Ώρες
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)

    # ΤΑΜΕΙΟ (από φύλλο "Ταμείο" – Είδος Έργου / Ποσό)
    c.execute("""
        CREATE TABLE IF NOT EXISTS fee_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_type TEXT,                 -- Είδος Έργου
            amount REAL                     -- Ποσό (€)
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
# ΣΕΛΙΔΑ ΠΕΛΑΤΩΝ / ΕΡΓΟΔΟΤΩΝ
# ------------------------------------------------------------

def page_clients():
    st.subheader("Εργοδότες / Πελάτες")

    with st.form("client_form"):
        st.markdown("### Νέος εργοδότης")

        col1, col2, col3 = st.columns(3)
        with col1:
            company_name = st.text_input("Επωνυμία")
            last_name = st.text_input("Επίθετο")
            first_name = st.text_input("Όνομα")
            entity_type = st.text_input("Σύσταση (π.χ. ΦΠ/ΕΠΕ/ΙΚΕ)")
        with col2:
            address = st.text_input("Διεύθυνση")
            postal_code = st.text_input("ΤΚ")
            city = st.text_input("Πόλη")
        with col3:
            phone_landline = st.text_input("Σταθερό")
            phone_mobile = st.text_input("Κινητό")
            email = st.text_input("Email")

        col4, col5, col6 = st.columns(3)
        with col4:
            afm = st.text_input("ΑΦΜ")
            dou = st.text_input("ΔΟΥ")
        with col5:
            job = st.text_input("Επάγγελμα")
        with col6:
            taxis_username = st.text_input("TaxisNet Username")
            taxis_password = st.text_input("TaxisNet Password", type="password")

        submitted = st.form_submit_button("Αποθήκευση εργοδότη")

        if submitted:
            execute("""
                INSERT INTO clients (
                    company_name, last_name, first_name, entity_type,
                    address, postal_code, city,
                    phone_landline, phone_mobile, email,
                    afm, dou, taxis_username, taxis_password, job
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                company_name, last_name, first_name, entity_type,
                address, postal_code, city,
                phone_landline, phone_mobile, email,
                afm, dou, taxis_username, taxis_password, job
            ))
            st.success("Ο εργοδότης αποθηκεύτηκε.")

    st.markdown("---")
    st.markdown("### Λίστα εργοδοτών")

    rows = fetch_all("""
        SELECT id, company_name, last_name, first_name,
               city, phone_mobile, afm, dou
        FROM clients
        ORDER BY company_name, last_name, first_name
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "company_name": "Επωνυμία",
            "last_name": "Επίθετο",
            "first_name": "Όνομα",
            "city": "Πόλη",
            "phone_mobile": "Κινητό",
            "afm": "ΑΦΜ",
            "dou": "ΔΟΥ"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εργοδότες.")


# ------------------------------------------------------------
# ΣΕΛΙΔΑ ΠΡΟΜΗΘΕΥΤΩΝ
# ------------------------------------------------------------

def page_suppliers():
    st.subheader("Προμηθευτές")

    with st.form("supplier_form"):
        st.markdown("### Νέος προμηθευτής / συνεργείο")

        col1, col2, col3 = st.columns(3)
        with col1:
            company_name = st.text_input("Επωνυμία Εταιρίας")
            last_name = st.text_input("Επίθετο")
            first_name = st.text_input("Όνομα")
            entity_type = st.text_input("Σύσταση")
            job = st.text_input("Επάγγελμα")
        with col2:
            iban1 = st.text_input("ΙΒΑΝ 1")
            bank1 = st.text_input("Τράπεζα 1")
            iban2 = st.text_input("ΙΒΑΝ 2")
            bank2 = st.text_input("Τράπεζα 2")
        with col3:
            iban3 = st.text_input("ΙΒΑΝ 3")
            bank3 = st.text_input("Τράπεζα 3")
            iban4 = st.text_input("ΙΒΑΝ 4")
            bank4 = st.text_input("Τράπεζα 4")

        col4, col5, col6 = st.columns(3)
        with col4:
            address = st.text_input("Διεύθυνση")
            postal_code = st.text_input("ΤΚ")
            city = st.text_input("Πόλη")
        with col5:
            phone1 = st.text_input("Τηλ. 1")
            phone2 = st.text_input("Τηλ. 2")
        with col6:
            email = st.text_input("Email")
            afm = st.text_input("ΑΦΜ")
            dou = st.text_input("ΔΟΥ")

        submitted = st.form_submit_button("Αποθήκευση προμηθευτή")

        if submitted:
            execute("""
                INSERT INTO suppliers (
                    company_name, last_name, first_name, entity_type, job,
                    iban1, bank1, iban2, bank2, iban3, bank3, iban4, bank4,
                    address, postal_code, city,
                    phone1, phone2, email, afm, dou
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                company_name, last_name, first_name, entity_type, job,
                iban1, bank1, iban2, bank2, iban3, bank3, iban4, bank4,
                address, postal_code, city,
                phone1, phone2, email, afm, dou
            ))
            st.success("Ο προμηθευτής αποθηκεύτηκε.")

    st.markdown("---")
    st.markdown("### Λίστα προμηθευτών")

    rows = fetch_all("""
        SELECT id, company_name, job, city, phone1, afm, dou
        FROM suppliers
        ORDER BY company_name
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "company_name": "Επωνυμία",
            "job": "Επάγγελμα",
            "city": "Πόλη",
            "phone1": "Τηλ. 1",
            "afm": "ΑΦΜ",
            "dou": "ΔΟΥ"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν προμηθευτές.")


# ------------------------------------------------------------
# ΣΕΛΙΔΑ ΕΡΓΩΝ
# ------------------------------------------------------------

def page_projects():
    st.subheader("Έργα")

    clients = fetch_all("SELECT id, company_name, last_name, first_name FROM clients ORDER BY company_name, last_name, first_name")
    client_options = ["— Χωρίς εργοδότη —"]
    client_map = {}
    for r in clients:
        label = (r["company_name"] or "").strip()
        if not label:
            label = f"{(r['last_name'] or '').strip()} {(r['first_name'] or '').strip()}".strip()
        if not label:
            label = f"ID {r['id']}"
        client_options.append(label)
        client_map[label] = r["id"]

    with st.form("project_form"):
        st.markdown("### Νέο έργο")

        col1, col2, col3 = st.columns(3)
        with col1:
            code = st.text_input("Κωδικός Έργου")
            reg_date = st.date_input("Ημ/νια Εγγραφής", value=date.today())
            protocol_no = st.text_input("Αρ. πρωτ")
        with col2:
            client_label = st.selectbox("Εργοδότης (από λίστα)", client_options)
            employer_name = st.text_input("Εργοδότης (ελεύθερο κείμενο)")
            hf_flag = st.text_input("ΗΦ-Φ")
        with col3:
            project_type = st.text_input("Είδος Έργου")
            priority = st.text_input("Προτεραιότητα")
            status = st.text_input("Κατάσταση")
            status2 = st.text_input("Κατάσταση2")

        col4, col5, col6 = st.columns(3)
        with col4:
            description = st.text_area("Περιγραφή", height=80)
        with col5:
            address = st.text_input("Διεύθυνση έργου")
            postal_code = st.text_input("ΤΚ")
            city = st.text_input("Πόλη")
        with col6:
            agreed_amount = st.number_input("Συμφωνημένη Αξία (€)", min_value=0.0, step=100.0, format="%.2f")
            invoice_expenses = st.number_input("Έξοδα παραστατικών (€)", min_value=0.0, step=10.0, format="%.2f")
            engineer = st.text_input("Μηχανικός")
            apy = st.text_input("ΑΠΥ")
            manager = st.text_input("Μάνος-Θανάσης")

        submitted = st.form_submit_button("Αποθήκευση έργου")

        if submitted:
            client_id = None
            if client_label in client_map:
                client_id = client_map[client_label]
            execute("""
                INSERT INTO projects (
                    code, reg_date, protocol_no, client_id, employer_name,
                    hf_flag, project_type, priority, status, status2,
                    description, address, postal_code, city,
                    agreed_amount, invoice_expenses,
                    engineer, apy, manager
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                code,
                reg_date.isoformat() if reg_date else None,
                protocol_no,
                client_id,
                employer_name,
                hf_flag,
                project_type,
                priority,
                status,
                status2,
                description,
                address,
                postal_code,
                city,
                agreed_amount,
                invoice_expenses,
                engineer,
                apy,
                manager
            ))
            st.success("Το έργο αποθηκεύτηκε.")

    st.markdown("---")
    st.markdown("### Λίστα έργων")

    rows = fetch_all("""
        SELECT p.id, p.code, p.reg_date, p.employer_name,
               p.project_type, p.status, p.city, p.agreed_amount
        FROM projects p
        ORDER BY p.reg_date DESC, p.id DESC
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "code": "Κωδικός",
            "reg_date": "Ημ/νια εγγραφής",
            "employer_name": "Εργοδότης",
            "project_type": "Είδος Έργου",
            "status": "Κατάσταση",
            "city": "Πόλη",
            "agreed_amount": "Συμφωνημένη Αξία (€)"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν έργα.")


# ------------------------------------------------------------
# ΣΕΛΙΔΑ ΠΑΡΑΣΤΑΤΙΚΩΝ (από φύλλο "Παραστατικά")
# ------------------------------------------------------------

def page_documents():
    st.subheader("Παραστατικά / Κινήσεις")

    projects = fetch_all("SELECT id, code, employer_name FROM projects ORDER BY reg_date DESC")
    project_options = ["— Χωρίς έργο —"]
    project_map = {}
    for r in projects:
        label = f"{r['code'] or ''} : {r['employer_name'] or ''}".strip(" :")
        if not label:
            label = f"Έργο {r['id']}"
        project_options.append(label)
        project_map[label] = r["id"]

    suppliers = fetch_all("SELECT id, company_name FROM suppliers ORDER BY company_name")
    supplier_options = ["— Χωρίς προμηθευτή —"]
    supplier_map = {}
    for r in suppliers:
        label = r["company_name"] or f"Προμηθευτής {r['id']}"
        supplier_options.append(label)
        supplier_map[label] = r["id"]

    with st.form("doc_form"):
        st.markdown("### Νέο παραστατικό")

        col1, col2, col3 = st.columns(3)
        with col1:
            seq_no = st.number_input("α/α", min_value=0, step=1)
            doc_date = st.date_input("Ημ/νία Παρ/τικού", value=date.today())
            project_label = st.selectbox("Έργο", project_options)
        with col2:
            billing_type = st.text_input("Τιμολόγηση")
            supplier_label = st.selectbox("Προμηθευτής - Συνεργείο", supplier_options)
            work_title = st.text_input("Εργασία")
        with col3:
            description = st.text_input("Περιγραφή")
            charge = st.number_input("Χρέωση (€)", min_value=0.0, step=10.0, format="%.2f")
            vat = st.number_input("ΦΠΑ (€)", min_value=0.0, step=10.0, format="%.2f")
            credit = st.number_input("Πίστωση (€)", min_value=0.0, step=10.0, format="%.2f")

        col4, col5, col6 = st.columns(3)
        with col4:
            payment_method = st.text_input("Τρόπος Πληρωμής")
        with col5:
            payments = st.number_input("Καταβολές (€)", min_value=0.0, step=10.0, format="%.2f")
        with col6:
            payment_target = st.text_input("Πού καταβλήθηκαν")
            day_val = st.text_input("ΗΜΕΡΑ", value=str(doc_date.day))
            month_val = st.text_input("ΜΗΝΑ", value=str(doc_date.month))
            year_val = st.text_input("ΕΤΟΣ", value=str(doc_date.year))

        submitted = st.form_submit_button("Αποθήκευση παραστατικού")

        if submitted:
            project_id = None
            if project_label in project_map:
                project_id = project_map[project_label]
            supplier_id = None
            if supplier_label in supplier_map:
                supplier_id = supplier_map[supplier_label]

            execute("""
                INSERT INTO documents (
                    seq_no, doc_date, project_id, billing_type,
                    supplier_id, work_title, description,
                    charge, vat, credit,
                    payment_method, payments, payment_target,
                    day, month, year
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                int(seq_no) if seq_no else None,
                doc_date.isoformat() if doc_date else None,
                project_id,
                billing_type,
                supplier_id,
                work_title,
                description,
                charge,
                vat,
                credit,
                payment_method,
                payments,
                payment_target,
                day_val,
                month_val,
                year_val
            ))
            st.success("Το παραστατικό αποθηκεύτηκε.")

    st.markdown("---")
    st.markdown("### Τελευταία παραστατικά")

    rows = fetch_all("""
        SELECT d.id, d.seq_no, d.doc_date,
               p.code AS project_code,
               p.employer_name,
               s.company_name AS supplier_name,
               d.work_title, d.charge, d.vat, d.credit
        FROM documents d
        LEFT JOIN projects p ON d.project_id = p.id
        LEFT JOIN suppliers s ON d.supplier_id = s.id
        ORDER BY d.doc_date DESC, d.id DESC
        LIMIT 200
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "seq_no": "α/α",
            "doc_date": "Ημ/νία",
            "project_code": "Κωδ. έργου",
            "employer_name": "Εργοδότης",
            "supplier_name": "Προμηθευτής",
            "work_title": "Εργασία",
            "charge": "Χρέωση (€)",
            "vat": "ΦΠΑ (€)",
            "credit": "Πίστωση (€)"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν παραστατικά.")


# ------------------------------------------------------------
# ΣΕΛΙΔΑ ΗΜΕΡΟΛΟΓΙΟΥ
# ------------------------------------------------------------

def page_worklog():
    st.subheader("Ημερολόγιο εργασιών")

    projects = fetch_all("SELECT id, code, employer_name FROM projects ORDER BY reg_date DESC")
    project_options = ["— Χωρίς έργο —"]
    project_map = {}
    for r in projects:
        label = f"{r['code'] or ''} : {r['employer_name'] or ''}".strip(" :")
        if not label:
            label = f"Έργο {r['id']}"
        project_options.append(label)
        project_map[label] = r["id"]

    with st.form("worklog_form"):
        st.markdown("### Νέα εγγραφή ημερολογίου")

        col1, col2, col3 = st.columns(3)
        with col1:
            log_date = st.date_input("Ημερομηνία", value=date.today())
        with col2:
            employee = st.text_input("Υπάλληλος")
            project_label = st.selectbox("Έργο", project_options)
        with col3:
            work_desc = st.text_input("Εργασία")
            hours = st.number_input("Ώρες", min_value=0.0, step=0.5)

        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            project_id = None
            if project_label in project_map:
                project_id = project_map[project_label]
            execute("""
                INSERT INTO worklog (log_date, employee, project_id, work_desc, hours)
                VALUES (?,?,?,?,?)
            """, (
                log_date.isoformat() if log_date else None,
                employee,
                project_id,
                work_desc,
                hours
            ))
            st.success("Η εγγραφή ημερολογίου αποθηκεύτηκε.")

    st.markdown("---")
    st.markdown("### Πρόσφατες εγγραφές")

    rows = fetch_all("""
        SELECT w.id, w.log_date, w.employee, p.code AS project_code,
               p.employer_name, w.work_desc, w.hours
        FROM worklog w
        LEFT JOIN projects p ON w.project_id = p.id
        ORDER BY w.log_date DESC, w.id DESC
        LIMIT 200
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "log_date": "Ημερομηνία",
            "employee": "Υπάλληλος",
            "project_code": "Κωδ. έργου",
            "employer_name": "Εργοδότης",
            "work_desc": "Εργασία",
            "hours": "Ώρες"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εγγραφές ημερολογίου.")


# ------------------------------------------------------------
# ΣΕΛΙΔΑ ΤΑΜΕΙΟΥ (template Είδος Έργου / Ποσό)
# ------------------------------------------------------------

def page_fee_templates():
    st.subheader("Ταμείο – Πρότυπα ποσά ανά είδος έργου")

    with st.form("fee_form"):
        st.markdown("### Νέο είδος έργου")

        col1, col2 = st.columns(2)
        with col1:
            work_type = st.text_input("Είδος έργου")
        with col2:
            amount = st.number_input("Ποσό (€)", min_value=0.0, step=100.0, format="%.2f")

        submitted = st.form_submit_button("Αποθήκευση")

        if submitted:
            execute("""
                INSERT INTO fee_templates (work_type, amount)
                VALUES (?,?)
            """, (work_type, amount))
            st.success("Το είδος έργου αποθηκεύτηκε στο Ταμείο.")

    st.markdown("---")
    st.markdown("### Λίστα ειδών έργου & ποσών")

    rows = fetch_all("""
        SELECT id, work_type, amount
        FROM fee_templates
        ORDER BY work_type
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "work_type": "Είδος έργου",
            "amount": "Ποσό (€)"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένα είδη έργου.")


# ------------------------------------------------------------
# ΑΠΛΕΣ ΑΝΑΦΟΡΕΣ
# ------------------------------------------------------------

def page_reports():
    st.subheader("Αναφορές")

    st.markdown("### Υπόλοιπα προμηθευτών (χειροκίνητα πεδία)")

    rows = fetch_all("""
        SELECT s.company_name,
               IFNULL(SUM(
                   COALESCE(d.charge,0) + COALESCE(d.vat,0)
                   - COALESCE(d.credit,0)
                   - COALESCE(d.payments,0)
               ), 0) AS balance
        FROM suppliers s
        LEFT JOIN documents d ON d.supplier_id = s.id
        GROUP BY s.id, s.company_name
        ORDER BY s.company_name
    """)

    if rows:
        df = pd.DataFrame(rows)
        df.rename(columns={
            "company_name": "Προμηθευτής",
            "balance": "Υπόλοιπο (€)"
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν ακόμη παραστατικά για υπολογισμό υπολοίπων.")

    st.markdown("---")
    st.markdown("### Σύνολο χρεώσεων ανά έργο")

    rows2 = fetch_all("""
        SELECT p.code, p.employer_name,
               IFNULL(SUM(COALESCE(d.charge,0) + COALESCE(d.vat,0)),0) AS total_cost
        FROM projects p
        LEFT JOIN documents d ON d.project_id = p.id
        GROUP BY p.id, p.code, p.employer_name
        ORDER BY p.reg_date DESC
    """)

    if rows2:
        df2 = pd.DataFrame(rows2)
        df2.rename(columns={
            "code": "Κωδ. έργου",
            "employer_name": "Εργοδότης",
            "total_cost": "Σύνολο Χρεώσεων+ΦΠΑ (€)"
        }, inplace=True)
        st.dataframe(df2, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν ακόμη παραστατικά ανά έργο.")


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------

def page_dashboard():
    st.subheader("Dashboard έργων")

    rows = fetch_all("""
        SELECT p.id, p.code, p.employer_name,
               IFNULL(SUM(COALESCE(d.charge,0) + COALESCE(d.vat,0)),0) AS total_cost,
               p.agreed_amount
        FROM projects p
        LEFT JOIN documents d ON d.project_id = p.id
        GROUP BY p.id, p.code, p.employer_name, p.agreed_amount
        ORDER BY p.reg_date DESC
    """)

    if rows:
        data = []
        for r in rows:
            agreed = r["agreed_amount"] or 0
            cost = r["total_cost"] or 0
            margin = agreed - cost
            data.append({
                "Κωδ. έργου": r["code"],
                "Εργοδότης": r["employer_name"],
                "Συμφωνημένη Αξία (€)": round(agreed, 2),
                "Σύνολο χρεώσεων+ΦΠΑ (€)": round(cost, 2),
                "Περιθώριο (€)": round(margin, 2)
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν ακόμη έργα με κινήσεις.")


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------

def main():
    st.set_page_config(page_title="Complete Construction – Διαχείριση έργων", layout="wide")
    st.title("Complete Construction – Διαχείριση έργων, πελατών & προμηθευτών")

    tabs = st.tabs([
        "Εργοδότες",
        "Προμηθευτές",
        "Έργα",
        "Παραστατικά",
        "Ημερολόγιο",
        "Ταμείο",
        "Αναφορές",
        "Dashboard"
    ])

    with tabs[0]:
        page_clients()
    with tabs[1]:
        page_suppliers()
    with tabs[2]:
        page_projects()
    with tabs[3]:
        page_documents()
    with tabs[4]:
        page_worklog()
    with tabs[5]:
        page_fee_templates()
    with tabs[6]:
        page_reports()
    with tabs[7]:
        page_dashboard()


# Εκκίνηση
init_db()
main()
