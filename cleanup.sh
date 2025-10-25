#!/bin/bash

# Cleanup Script for Bengali Speech Audio-Visual Dataset
# ======================================================
# Removes unnecessary files and organizes the directory structure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "========================================="
print_status "Cleaning up project directory..."
print_status "========================================="

# Remove old/duplicate pipeline files
print_status "Removing duplicate pipeline files..."
if [ -f "run_transcription_pipeline_old.py" ]; then
    rm "run_transcription_pipeline_old.py"
    print_success "Removed run_transcription_pipeline_old.py"
fi

if [ -f "run_transcription_pipeline.py" ]; then
    # Check if it's different from modular version
    if [ -f "run_transcription_pipeline_modular.py" ]; then
        print_warning "Found both run_transcription_pipeline.py and run_transcription_pipeline_modular.py"
        print_status "Keeping the modular version, removing the old one"
        rm "run_transcription_pipeline.py"
        print_success "Removed run_transcription_pipeline.py"
    fi
fi

# Clean up old log files (keep recent ones)
print_status "Cleaning up old log files..."
find . -name "*.log" -mtime +30 -type f -delete 2>/dev/null || true
print_success "Cleaned old log files (>30 days)"

# Remove temporary/cache files
print_status "Removing cache and temporary files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -delete 2>/dev/null || true
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
find . -name "*.tmp" -type f -delete 2>/dev/null || true
print_success "Removed cache and temporary files"

# Clean up empty directories
print_status "Removing empty directories..."
find . -type d -empty -delete 2>/dev/null || true
print_success "Removed empty directories"

# Organize processed audio files (optional)
if [ -d "amplified_denoised_audio" ] && [ -d "denoised_audio" ]; then
    print_warning "Found both amplified_denoised_audio and denoised_audio directories"
    print_status "Consider consolidating these if they contain duplicate files"
fi

# Check for large files that might be temporary
print_status "Checking for large temporary files..."
large_files=$(find . -size +100M -type f 2>/dev/null | grep -E '\.(tmp|temp|log)$' || true)
if [ ! -z "$large_files" ]; then
    print_warning "Found large temporary files:"
    echo "$large_files"
    print_status "Consider removing these manually if they're not needed"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    print_status "Creating .gitignore file..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
*.tmp
*.temp
outputs/*/temp/
logs/*.log
.env

# Audio/Video files (large)
*.wav
*.mp4
*.avi
*.mov
*.mkv

# Except sample data
!sample_data/**/*.wav
!sample_data/**/*.mp4
EOF
    print_success "Created .gitignore file"
fi

print_status "========================================="
print_success "Cleanup completed!"
print_status "========================================="

print_status "Summary of cleaned items:"
print_status "  ✅ Removed duplicate pipeline files"
print_status "  ✅ Cleaned old log files (>30 days)"
print_status "  ✅ Removed Python cache files"
print_status "  ✅ Removed system temp files"
print_status "  ✅ Removed empty directories"
print_status "  ✅ Created/updated .gitignore"

print_warning "Note: Large video/audio files in outputs/ are preserved"
print_warning "Consider cleaning them manually if disk space is needed"