# Scripts

Utility scripts for deployment, maintenance, and data management.

## Deployment

### `prepare_deployment.py`
Prepare the project for Render deployment.
```bash
python scripts/prepare_deployment.py
```

### `quick_deploy.sh`
Quick deployment to Render.
```bash
./scripts/quick_deploy.sh
```

### `setup_render_env.sh`
Setup environment variables for Render.
```bash
source scripts/setup_render_env.sh
```

## Maintenance

### `maintenance.sh`
Run maintenance tasks.
```bash
./scripts/maintenance.sh backup    # Create backup
./scripts/maintenance.sh verify    # Verify deployment
./scripts/maintenance.sh health    # Check data health
./scripts/maintenance.sh fix       # Fix common issues
./scripts/maintenance.sh prepare   # Prepare deployment
./scripts/maintenance.sh clean     # Clean old backups
./scripts/maintenance.sh update    # Update dependencies
./scripts/maintenance.sh test      # Run tests
```

## Data Management

### `check_data_health.py`
Check data integrity and health.
```bash
python scripts/check_data_health.py
```

### `fix_common_issues.py`
Fix common data issues automatically.
```bash
python scripts/fix_common_issues.py --dry-run  # Preview changes
python scripts/fix_common_issues.py            # Apply fixes
```

## Common Workflows

### Before Deployment
```bash
# 1. Check data health
python scripts/check_data_health.py

# 2. Fix any issues
python scripts/fix_common_issues.py

# 3. Prepare deployment
python scripts/prepare_deployment.py

# 4. Deploy
./scripts/quick_deploy.sh
```

### After Deployment
```bash
# 1. Verify deployment
python manage.py verify_deployment

# 2. Check health
python scripts/check_data_health.py

# 3. View logs
render logs --service your-service-name
```

### Regular Maintenance
```bash
# Weekly
./scripts/maintenance.sh backup
./scripts/maintenance.sh health

# Monthly
./scripts/maintenance.sh clean
./scripts/maintenance.sh update
```
