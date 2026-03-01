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

## Student Profile Rules
- `College Roll No` is admin-controlled and fixed for each student.
- Students can view their roll number in the profile, but they cannot edit it.
- For any roll number correction, contact the Exam Cell/Admin.

## How Users Verify Email and Phone (OTP)
1. Login as a student and open `Student Portal -> Settings` (`/student/portal/profile/`).
2. In `Personal Email (OTP)` or `Personal Phone (OTP)`, enter the value you want to verify.
3. Click `Send OTP`.
4. Check your inbox/SMS, enter the 6-digit OTP in the input box.
5. Click `Verify`.
6. Status changes from `Not Verified` to `Verified`.

### OTP Delivery Setup (for realtime delivery)
- Email OTP uses Django email backend (`DEFAULT_FROM_EMAIL` and SMTP/email settings in `.env`).
- SMS OTP uses Twilio when configured:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
- Or a generic SMS API:
  - `SMS_API_URL`
  - optional `SMS_API_TOKEN`, `SMS_API_PHONE_FIELD`, `SMS_API_MESSAGE_FIELD`
