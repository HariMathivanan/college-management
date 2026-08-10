# Alumni Management System
A full-featured web app built with **Flask + MySQL**.

## Features
| Module | What it does |
|---|---|
| 🔐 Auth | Register, Login, Role-based access (Admin / Alumni) |
| 👥 Alumni Directory | Search, filter by batch/department, view profiles |
| 👤 Profile | Each alumni can edit their own profile |
| 📅 Events | Admins post events; all users view them |
| 💼 Job Board | Any alumni can post/delete jobs |
| 📰 News | Admins publish announcements |
| 🛡️ Admin Panel | Manage all users, toggle roles, delete accounts |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL
```bash
mysql -u root -p < schema.sql
```

> If you already have the database from a previous version, update the donations table to add the new fields before using the donation form.
> ```sql
> ALTER TABLE donations ADD COLUMN payment_method VARCHAR(50);
> ALTER TABLE donations ADD COLUMN donation_type VARCHAR(150);
> ALTER TABLE donations ADD COLUMN phone VARCHAR(30);
> ALTER TABLE donations ADD COLUMN donation_status VARCHAR(50) DEFAULT 'Pending';
> ```
>
> To add donation distribution support for staff:
> ```sql
> CREATE TABLE IF NOT EXISTS donation_allocations (
>     id INT AUTO_INCREMENT PRIMARY KEY,
>     donation_id INT NOT NULL,
>     student_id INT NOT NULL,
>     allocated_by INT NULL,
>     amount DECIMAL(10,2) NOT NULL,
>     note TEXT,
>     claimed BOOLEAN DEFAULT 0,
>     claimed_at TIMESTAMP NULL,
>     allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
>     FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
>     FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
>     FOREIGN KEY (allocated_by) REFERENCES users(id) ON DELETE SET NULL
> );
> ```

### 3. Configure database
This app uses MySQL. Make sure your MySQL server is installed and running before starting the app.

Use environment variables or edit `config.py`:
```bash
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASSWORD=your_password
set DB_NAME=alumni_db
```

Or update the values directly in `config.py`.

### 4. Run the app
```bash
python app.py
```

Open http://localhost:5000

## Publishing Safely

Before pushing this project to a public repository:

- Add a `.gitignore` to exclude local envs and caches (included in this repo).
- Copy `.env.example` to `.env` and fill real credentials locally; never commit `.env`.
- Use your Git host's secret store / CI variables for deployment secrets (do not put them in source).
- If secrets were committed previously, remove them from git history (use `git filter-repo` or BFG) and rotate those credentials immediately.
- Consider adding a license (e.g., MIT) and a short `CONTRIBUTING.md` if you want others to collaborate.

If you want, I can create a `.gitignore` and `.env.example` for you (already added), and prepare a short commit message or help remove secrets from git history.

## Admin Account
- **Email:** admin@alumni.com (example)
- **Password:** Do NOT store or distribute plaintext passwords. Create an admin user by registering through the app or insert a user with a hashed password into the database.

## Project Structure
```
alumni_management/
├── app.py               # Flask routes & logic
├── schema.sql           # MySQL database schema + seed data
├── requirements.txt
└── templates/
    ├── base.html        # Sidebar layout
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── alumni_list.html
    ├── alumni_detail.html
    ├── profile.html
    ├── events.html
    ├── add_event.html
    ├── jobs.html
    ├── add_job.html
    ├── news.html
    ├── add_news.html
    └── admin_users.html
```
"College Management" 
"# college-management" 
