# IC UrFU Odoo Module

Custom Odoo 17.0 module for Ural Federal University (UrFU) that generates individual educational plan documents for master's students.

## ✨ Features

- 📄 Generate individual education plan documents in DOCX format
- ✅ Follows UrFU's official formatting requirements
- 👥 Role-based access control (Student & Teacher)
- 📚 Support for mandatory and elective subjects
- 🔄 Workflow: Draft → Submit → Review → Approve → Generate
- 🐳 Fully dockerized development environment
- 🚀 One-command initialization

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Git

### Installation (One Command!)

```bash
# Clone the repository
git clone <repository-url>
cd ic-urfu-odoo-module

# Initialize the project (single command!)
make init
```

**That's it!** The `make init` command will:
1. ✅ Start Docker containers (Odoo 17 + PostgreSQL 17)
2. ✅ Wait for services to be ready
3. ✅ Initialize the database
4. ✅ Install the module with demo data
5. ✅ Create student and teacher accounts
6. ✅ **Synchronize passwords from `ic_urfu_module/config/demo_credentials.py`**
7. ✅ Load demo subjects and plans

### For Complete Reset

If you want to start completely fresh (deletes all data):

```bash
make bootstrap
```

This will ask for confirmation, then clean everything and reinitialize.

### Access the Application

Open your browser and navigate to:
**http://localhost:8079**

## 🔐 Demo Accounts

After initialization, you can login with these accounts:

| Role    | Login   | Password | Email               |
| ------- | ------- | -------- | ------------------- |
| Student | student | student  | student@example.com |
| Teacher | teacher | teacher  | teacher@example.com |

**Want to change passwords?** See [docs/CREDENTIALS.md](docs/CREDENTIALS.md) for instructions.

All credentials are stored in one place: `ic_urfu_module/config/demo_credentials.py`

## 📦 What's Included in Demo Data

The initialization automatically loads:

- ✅ **7 Mandatory Subjects**
  - Философские проблемы науки и техники
  - Иностранный язык в профессиональной коммуникации
  - Методология научных исследований
  - Современные технологии программирования
  - Архитектура программных систем
  - Управление проектами в IT
  - Научно-исследовательская работа

- ✅ **6 Elective Subjects**
  - Машинное обучение
  - Blockchain технологии
  - Облачные вычисления
  - Анализ больших данных
  - Мобильная разработка
  - Компьютерное зрение

- ✅ **1 Demo Plan** for student (4 semesters with subjects)

## 🛠 Available Commands

```bash
make help               # Show all available commands
make bootstrap          # 🚀 Complete setup from scratch (clean + init)
make init               # Initialize project (single entry point!)
make start              # Start Docker containers
make stop               # Stop Docker containers
make restart            # Restart Docker containers
make logs               # View Odoo logs (Ctrl+C to exit)
make status             # Check containers status
make shell              # Open shell in Odoo container
make db-shell           # Open PostgreSQL shell
make test-generator     # Test document generator standalone
make update-credentials # Regenerate demo_users.xml from credentials config
make fix-passwords      # Fix user passwords if login fails
make clean              # Remove all data and start fresh
```

**Single entry point:** `make init` - guarantees working credentials!

**To change passwords**: Edit `ic_urfu_module/config/demo_credentials.py` and run `make init`

**If you can't login**: Run `make fix-passwords` to reset passwords to default values

## 📖 How to Use

### As a Student

1. Login with `student` / `student`
2. Navigate to **IC UrFU** menu
3. Create a new Individual Plan
4. Fill in your information
5. Add semesters and select subjects
6. Submit the plan for teacher review

### As a Teacher

1. Login with `teacher` / `teacher`
2. Navigate to **IC UrFU** menu → **Individual Plans**
3. Review submitted plans
4. Approve or reject with comments
5. Approved plans can be used to generate documents

### Generate Document

Once a plan is approved:
1. Open the approved plan
2. Click **Generate Document** button
3. Download the generated DOCX file

## 📁 Project Structure

```
ic-urfu-odoo-module/
├── ic_urfu_module/           # Odoo module
│   ├── models/               # ORM models (Subject, Semester, IndividualPlan)
│   ├── views/                # XML views and menus
│   ├── security/             # Access control (groups, rules, permissions)
│   ├── demo/                 # Demo data (users, subjects, plans)
│   ├── doc_generator/        # DOCX document generator
│   └── __manifest__.py       # Module metadata
├── local-env/                # Docker environment
│   ├── docker-compose.yml    # Docker services configuration
│   ├── Dockerfile            # Odoo container setup
│   ├── odoo.conf             # Odoo configuration
│   └── load_demo_data.py     # Script to load demo data
├── scripts/                  # Helper scripts
│   └── init.sh               # Initialization script
├── Makefile                  # Make commands
└── README.md                 # This file
```

## 🔧 Development

### Running Locally

```bash
# Start containers
make start

# View logs
make logs

# Access Odoo shell (for debugging)
make shell

# Access database
make db-shell
```

### Testing Document Generator

The document generator can be tested independently:

```bash
make test-generator
```

This will generate a sample DOCX file using test data.

### Environment Details

- **Odoo**: http://localhost:8079
- **PostgreSQL**: localhost:2345
  - Database: `odoo`
  - User: `odoo`
  - Password: `odoo`

## 🔄 Workflow States

Individual plans have the following workflow:

1. **Draft** - Student is creating/editing the plan
2. **Submitted** - Plan submitted for teacher review
3. **Approved** - Teacher approved the plan
4. **Rejected** - Teacher rejected with comments (returns to draft)
5. **Generated** - Final document has been generated

## 🚨 Troubleshooting

### Containers won't start

```bash
# Check if Docker is running
docker info

# Check container status
make status

# View logs for errors
make logs
```

### Database connection issues

```bash
# Check if PostgreSQL is ready
docker exec odoo_db pg_isready -U odoo

# Restart containers
make restart
```

### Module not installed

```bash
# Reinitialize (will preserve existing data if DB exists)
make init

# Or clean start (⚠️ DELETES ALL DATA)
make clean
make init
```

### Port already in use

If port 8079 or 2345 is already in use, edit `local-env/docker-compose.yml` and change the port mappings:

```yaml
# odoo service
ports:
  - "9069:8069"  # example: different host port for Odoo (container still 8069)

# db service
ports:
  - "3456:5432"  # example: different host port for PostgreSQL
```

### Can't login

Make sure you're using the correct credentials:
- Student: `student` / `student`
- Teacher: `teacher` / `teacher`

**Quick fix:** Run `make fix-passwords` to reset passwords to default values.

To change passwords, see [docs/CREDENTIALS.md](docs/CREDENTIALS.md)

If still having issues, reinitialize:

```bash
make clean
make init
```

## 🧹 Clean Slate

To completely remove everything and start fresh:

```bash
make clean
make init
```

**Warning:** This will delete all data including the database!

## 🎯 Next Steps

After successful initialization:

1. ✅ Explore the demo plan as a student
2. ✅ Try the teacher approval workflow
3. ✅ Generate a document from an approved plan
4. ✅ Create your own subjects
5. ✅ Customize the module for your needs

## 📝 Technical Details

- **Odoo Version**: 17.0
- **PostgreSQL Version**: 17
- **Python Dependencies**: python-docx
- **License**: LGPL-3

## 🤝 Contributing

This is a custom module for UrFU. For issues or contributions, please create an issue in the repository.

## 📄 License

LGPL-3 - See LICENSE file for details

---

**Made for Ural Federal University (UrFU)**