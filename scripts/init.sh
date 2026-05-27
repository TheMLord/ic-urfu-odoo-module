#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  IC UrFU Odoo Module - Initialization"
echo "=========================================="
echo ""

# Change to local-env directory
cd "$(dirname "$0")/../local-env" || exit 1

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${BLUE}[1/5] Starting Docker containers...${NC}"
docker compose up -d

echo ""
echo -e "${BLUE}[2/5] Waiting for PostgreSQL to be ready...${NC}"
echo -n "Waiting for database"
until docker exec odoo_db pg_isready -U odoo > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " ✓ Ready!"

echo ""
echo -e "${BLUE}[3/5] Waiting for Odoo to start...${NC}"
echo -n "Waiting for Odoo"
for i in {1..30}; do
    if docker logs odoo_app 2>&1 | grep -q "odoo.modules.loading.*Modules loaded"; then
        echo " ✓ Ready!"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}Warning: Odoo might not be fully ready yet. Check logs if needed:${NC}"
        echo "  docker logs odoo_app"
    fi
done

echo ""
echo -e "${BLUE}[4/5] Initializing Odoo database and installing module...${NC}"

# Check if database exists
DB_EXISTS=$(docker exec odoo_db psql -U odoo -lqt | cut -d \| -f 1 | grep -w odoo | wc -l | tr -d ' ')

if [ "$DB_EXISTS" -eq "0" ]; then
    echo "Creating database and installing module (this may take 2-3 minutes)..."

    # Initialize database with demo data (-i = install module and dependencies)
    docker exec odoo_app odoo -c /etc/odoo/odoo.conf -d odoo -i ic_urfu_module --stop-after-init --without-demo=False

    echo " ✓ Database created and install step finished."
else
    echo "Database already exists. Checking module status..."

    MODULE_INSTALLED=$(docker exec odoo_db psql -U odoo -d odoo -tAc "SELECT state FROM ir_module_module WHERE name='ic_urfu_module'" 2>/dev/null | tr -d '[:space:]' || echo "")

    if [ "$MODULE_INSTALLED" = "installed" ]; then
        echo " ✓ Module already installed!"
    else
        echo "Installing ic_urfu_module (previous state: ${MODULE_INSTALLED:-no row})..."
        docker exec odoo_app odoo -c /etc/odoo/odoo.conf -d odoo -i ic_urfu_module --stop-after-init --without-demo=False
        echo " ✓ Install step finished."
    fi
fi

MODULE_STATE=$(docker exec odoo_db psql -U odoo -d odoo -tAc "SELECT state FROM ir_module_module WHERE name='ic_urfu_module'" 2>/dev/null | tr -d '[:space:]' || echo "")
if [ -z "$MODULE_STATE" ] || [ "$MODULE_STATE" != "installed" ]; then
    echo -e "${RED}ERROR: ic_urfu_module is not installed (ir_module_module.state='${MODULE_STATE:-missing}').${NC}"
    echo "  Check Odoo output above and: docker logs odoo_app"
    echo "  Then run: ${YELLOW}make clean && make init${NC}  or install from Apps (enable Developer Mode → Update Apps List → search IC UrFU)."
    exit 1
fi

# Restart Odoo to ensure clean state
echo ""
echo -e "${BLUE}[5/6] Restarting Odoo...${NC}"
docker compose restart odoo
echo -n "Waiting for Odoo to restart"
sleep 5
for i in {1..15}; do
    if curl -s http://localhost:8079/web/database/selector > /dev/null 2>&1 || \
       curl -s http://localhost:8079/web/login > /dev/null 2>&1; then
        echo " ✓ Ready!"
        break
    fi
    echo -n "."
    sleep 2
done

# Load/update user credentials
echo ""
echo -e "${BLUE}[6/6] Synchronizing user credentials...${NC}"
docker exec -i odoo_app odoo shell -c /etc/odoo/odoo.conf -d odoo --no-http 2>&1 <<'PYEOF' | grep -E '(✓|✗|password)'
# Update student password
student = env['res.users'].search([('login', '=', 'student')], limit=1)
if student:
    student.write({'password': 'student'})
    print('✓ Student password updated')
else:
    print('✗ Student user not found')

# Update teacher password
teacher = env['res.users'].search([('login', '=', 'teacher')], limit=1)
if teacher:
    teacher.write({'password': 'teacher'})
    print('✓ Teacher password updated')
else:
    print('✗ Teacher user not found')

env.cr.commit()
print('✓ Credentials synchronized')
PYEOF

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Initialization Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Access Odoo at:${NC} http://localhost:8079"
echo ""
echo -e "${BLUE}Login: use res.users.login (student / teacher), not email:${NC}"
echo "  ┌────────────────────────────────────────────────────────┐"
echo "  │ Student — login: student    password: student          │"
echo "  │ Teacher — login: teacher    password: teacher          │"
echo "  └────────────────────────────────────────────────────────┘"
echo ""
echo -e "${BLUE}Apps:${NC} technical name is ${YELLOW}ic_urfu_module${NC}; display name ${YELLOW}IC UrFU Module${NC}."
echo ""
echo -e "${BLUE}Demo data loaded:${NC}"
echo "  ✓ 7 mandatory subjects"
echo "  ✓ 6 elective subjects"
echo "  ✓ 1 demo plan for student (4 semesters)"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  make logs      - View Odoo logs"
echo "  make stop      - Stop containers"
echo "  make clean     - Remove all data and start fresh"
echo ""
echo -e "${BLUE}To change passwords:${NC}"
echo "  1. Edit: ic_urfu_module/config/demo_credentials.py"
echo "  2. Run:  make clean && make init"
echo ""
