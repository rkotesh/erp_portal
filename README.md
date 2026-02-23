# College ERP — Enterprise Development

A comprehensive College ERP Web Application built using Django and the Antigravity development methodology.

## 🚀 Quick Start (Development)

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements/development.txt
   ```
3. **Configure Environment**:
   Create a `.env` file in the root directory (refer to `.env.example`).
4. **Setup Database**:
   ```bash
   python manage.py migrate
   python manage.py setup_roles
   python manage.py populate_dev_data
   ```
5. **Run the Server**:
   ```bash
   python manage.py runserver
   ```
6. **Run Tests**:
   ```bash
   python -m pytest
   ```

## 🛠 Tech Stack
- **Backend**: Django 5.x, DRF, Celery, Redis
- **Frontend**: HTMX, Chart.js, Vanilla CSS
- **Database**: PostgreSQL (Production), SQLite (Dev)
- **Monitoring**: Sentry, Prometheus/Grafana

## 📖 Key Sections (Rule Book Implementation)
- **RBAC**: Implemented in `apps.accounts`, configured via `setup_roles` command.
- **Service Layer**: Business logic in `apps.*.services`.
- **Selectors**: Read-only queries in `apps.*.selectors`.
- **Audit Logging**: Immutable logging in `apps.audit`.

## 📜 Documentation
API documentation is available at `/api/schema/swagger/` when the server is running.
