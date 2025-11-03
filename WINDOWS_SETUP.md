# 🪟 ArtScope Setup Guide for Windows

## Prerequisites Installation

### 1. Install Python 3.12
```powershell
# Download from python.org or use winget
winget install Python.Python.3.12

# Verify installation
python --version  # Should show Python 3.12.x
```

### 2. Install PostgreSQL (Optional - using Neon cloud)
You're already using Neon PostgreSQL, so local installation is optional.

If you want a local database for development:
```powershell
# Download from postgresql.org
# Or use chocolatey
choco install postgresql

# Add to PATH
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"
```

### 3. Install Redis for Windows
```powershell
# Option 1: Using Memurai (Redis for Windows)
winget install Memurai.Memurai

# Option 2: Using WSL2 + Ubuntu
wsl --install
wsl
sudo apt update
sudo apt install redis-server
redis-server --daemonize yes

# Verify Redis is running
redis-cli ping  # Should return PONG
```

### 4. Install Git (if not already)
```powershell
winget install Git.Git
```

## Project Setup

### Step 1: Navigate to Project Directory
```powershell
cd C:\Users\kp755\OneDrive\Desktop\RealMeta
```

### Step 2: Create Virtual Environment
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 3: Install Dependencies
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# This may take 5-10 minutes (installing PyTorch, CLIP, etc.)
```

**Note:** If you encounter issues with PyTorch on Windows:
```powershell
# Install PyTorch with CUDA support (if you have NVIDIA GPU)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Or CPU-only version (faster install, slower inference)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Configure Environment
```powershell
# Copy environment template
copy .env.example .env

# Edit .env (using notepad or VS Code)
notepad .env
```

**Required Settings:**
```env
SECRET_KEY=your-secret-key-here-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Your Neon Database (already configured!)
DATABASE_URL=postgresql://neondb_owner:npg_Qwn8HUECP4oz@ep-polished-glade-a1lfsvog-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# Redis (local)
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Generate a new SECRET_KEY:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Initialize Database
```powershell
# Run migrations
python manage.py migrate

# Initialize pgvector extension
python manage.py init_db

# Create superuser (admin account)
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

### Step 6: Load Sample Data (Optional)
```powershell
python manage.py create_sample_data
```

### Step 7: Start Development Servers

**Terminal 1 - Django Development Server:**
```powershell
cd C:\Users\kp755\OneDrive\Desktop\RealMeta
.\venv\Scripts\activate
python manage.py runserver
```

Server will start at: http://localhost:8000

**Terminal 2 - Celery Worker:**
```powershell
cd C:\Users\kp755\OneDrive\Desktop\RealMeta
.\venv\Scripts\activate

# Windows-specific Celery command (uses 'solo' pool)
celery -A artscope worker --loglevel=info --pool=solo
```

**Terminal 3 - Redis Server:**
```powershell
# If using Memurai
memurai

# If using WSL
wsl
redis-server
```

## Verification

### Test Django Server
Open browser: http://localhost:8000/admin
- Login with superuser credentials
- You should see the Django admin interface

### Test Redis
```powershell
redis-cli ping
# Should return: PONG
```

### Test Celery
```powershell
# In Python shell
python manage.py shell

# Run this code:
from embeddings.tasks import generate_artwork_embedding
result = generate_artwork_embedding.delay('test-id')
print(result.id)
```

### Test Database Connection
```powershell
python manage.py dbshell
```

Should connect to your Neon PostgreSQL database.

## Common Issues & Solutions

### Issue 1: "Redis connection failed"
**Solution:**
```powershell
# Make sure Redis is running
redis-cli ping

# If not running:
# For Memurai:
memurai

# For WSL:
wsl
sudo service redis-server start
```

### Issue 2: "ModuleNotFoundError: No module named 'X'"
**Solution:**
```powershell
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Issue 3: Celery fails to start on Windows
**Solution:**
```powershell
# Use solo pool (Windows compatible)
celery -A artscope worker --loglevel=info --pool=solo

# Or use eventlet
pip install eventlet
celery -A artscope worker --loglevel=info --pool=eventlet
```

### Issue 4: PyTorch installation takes too long
**Solution:**
```powershell
# Install CPU-only version (much smaller)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Issue 5: "psycopg2 installation failed"
**Solution:**
```powershell
# Use binary version
pip install psycopg2-binary --force-reinstall
```

### Issue 6: Port 8000 already in use
**Solution:**
```powershell
# Use different port
python manage.py runserver 8080

# Or find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Testing the Application

### 1. Access Admin Panel
```
URL: http://localhost:8000/admin
Login: Use superuser credentials
```

### 2. Create a Museum
- Click "Museums" → "Add Museum"
- Fill in required fields
- Save

### 3. Create an Artist
- Click "Artists" → "Add Artist"
- Fill in details
- Save

### 4. Create an Artwork
- Click "Artworks" → "Add Artwork"
- Select museum and artist
- Upload an image (IMPORTANT!)
- Fill in title and description
- Save

### 5. Test API Scanning

Using PowerShell:
```powershell
# Install curl if needed
winget install cURL.cURL

# Test scan endpoint
curl -X POST http://localhost:8000/api/scan/ `
  -F "image=@C:\path\to\artwork.jpg" `
  -F "museum_id=<museum-uuid-from-admin>"
```

Using Postman:
1. Import `postman_collection.json`
2. Set base_url to `http://localhost:8000`
3. Test endpoints

### 6. Check Celery Task
After creating artwork:
- Check Terminal 2 (Celery worker)
- Should see: "Embedding generated for artwork: ..."

## Development Workflow

### Starting Work
```powershell
# 1. Open VS Code
code C:\Users\kp755\OneDrive\Desktop\RealMeta

# 2. Open 3 terminals in VS Code

# Terminal 1: Django
.\venv\Scripts\activate
python manage.py runserver

# Terminal 2: Celery
.\venv\Scripts\activate
celery -A artscope worker --loglevel=info --pool=solo

# Terminal 3: Commands
.\venv\Scripts\activate
# Use for migrations, shell, etc.
```

### Making Changes
```powershell
# 1. Edit code in VS Code

# 2. If models changed:
python manage.py makemigrations
python manage.py migrate

# 3. Django auto-reloads on code changes

# 4. Restart Celery if tasks changed
# (Ctrl+C in Terminal 2, then restart)
```

### Stopping Work
```powershell
# In each terminal:
Ctrl+C

# Deactivate virtual environment
deactivate
```

## VS Code Configuration

### Recommended Extensions
- Python (Microsoft)
- Django (Baptiste Darthenay)
- REST Client
- SQLTools PostgreSQL

### VS Code Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true
  }
}
```

### VS Code Tasks (.vscode/tasks.json)
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Django: Run Server",
      "type": "shell",
      "command": "${workspaceFolder}\\venv\\Scripts\\python.exe",
      "args": ["manage.py", "runserver"],
      "problemMatcher": []
    },
    {
      "label": "Celery: Start Worker",
      "type": "shell",
      "command": "${workspaceFolder}\\venv\\Scripts\\celery.exe",
      "args": ["-A", "artscope", "worker", "--loglevel=info", "--pool=solo"],
      "problemMatcher": []
    }
  ]
}
```

## Performance Tips for Windows

1. **Use SSD for project directory**
   - Faster file I/O
   - Better for Celery and Redis

2. **Exclude venv from Windows Defender**
   ```powershell
   Add-MpPreference -ExclusionPath "C:\Users\kp755\OneDrive\Desktop\RealMeta\venv"
   ```

3. **Use Windows Terminal**
   ```powershell
   winget install Microsoft.WindowsTerminal
   ```

4. **Enable WSL2 for better performance**
   ```powershell
   wsl --install
   # Run Redis and Celery in WSL2
   ```

## Next Steps

1. ✅ Complete local setup
2. ✅ Test all API endpoints
3. ✅ Upload sample artworks
4. ✅ Test AR scanning
5. 🚀 Deploy to Render

## Deployment to Render

When ready to deploy:

1. Push code to GitHub
2. Connect Render to your repository
3. Set environment variables in Render dashboard
4. Deploy with automatic build

See `README.md` for detailed deployment instructions.

## Support

- Check `README.md` for detailed documentation
- Check `ARCHITECTURE.md` for system design
- Check `QUICKSTART.md` for quick reference

---

Happy coding on Windows! 🪟🎨
