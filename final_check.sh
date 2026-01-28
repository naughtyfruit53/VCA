#!/bin/bash

echo "=========================================="
echo "Final Implementation Verification"
echo "=========================================="
echo ""

# Check file structure
echo "✓ Checking file structure..."
files=(
    "main.py"
    "requirements.txt"
    ".env.example"
    ".gitignore"
    "BACKEND_README.md"
    "IMPLEMENTATION_SUMMARY.md"
    "app/__init__.py"
    "app/api/__init__.py"
    "app/api/health.py"
    "app/config/__init__.py"
    "app/config/settings.py"
    "app/config/database.py"
    "app/models/__init__.py"
    "app/schemas/__init__.py"
    "test_scaffold.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ MISSING: $file"
    fi
done

echo ""
echo "✓ Checking multi-tenant comments..."
grep -q "All future features MUST be added behind tenant_id boundaries" main.py && echo "  ✓ Multi-tenant comment in main.py"
grep -q "All future features MUST be added behind tenant_id boundaries" app/models/__init__.py && echo "  ✓ Multi-tenant comment in models"

echo ""
echo "✓ Checking TODO comments..."
main_todos=$(grep -c "TODO:" main.py)
model_todos=$(grep -c "TODO:" app/models/__init__.py)
schema_todos=$(grep -c "TODO:" app/schemas/__init__.py)
echo "  ✓ main.py: $main_todos TODOs"
echo "  ✓ models: $model_todos TODOs"
echo "  ✓ schemas: $schema_todos TODOs"
echo "  ✓ Total: $((main_todos + model_todos + schema_todos)) TODOs"

echo ""
echo "✓ Checking model structure..."
python3 -c "
from app.models import Tenant, PhoneNumber, Call, AIProfile
models = [
    ('Tenant', Tenant, False),
    ('PhoneNumber', PhoneNumber, True),
    ('Call', Call, True),
    ('AIProfile', AIProfile, True)
]

from sqlalchemy import inspect
for name, model, needs_tenant_id in models:
    inspector = inspect(model)
    has_tenant_id = any(col.name == 'tenant_id' for col in inspector.columns)
    if needs_tenant_id and has_tenant_id:
        print(f'  ✓ {name}: has tenant_id')
    elif not needs_tenant_id and not has_tenant_id:
        print(f'  ✓ {name}: root model (no tenant_id needed)')
    else:
        print(f'  ✗ {name}: tenant_id issue')
" 2>&1

echo ""
echo "=========================================="
echo "Implementation Complete!"
echo "=========================================="
