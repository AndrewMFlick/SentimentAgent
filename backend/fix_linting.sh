#!/bin/bash
# Auto-fix Python linting errors using autopep8 and autoflake

set -e

echo "🧹 Removing unused imports..."
python3 -m autoflake --in-place --remove-all-unused-imports --recursive src/

echo "📏 Fixing line length and PEP8 issues..."
python3 -m autopep8 --in-place --aggressive --aggressive --max-line-length 88 --recursive src/

echo "🎨 Formatting with black (88 char line length)..."
python3 -m black --line-length 88 src/

echo "📦 Sorting imports..."
python3 -m isort src/

echo "✅ Linting fixes complete!"
echo ""
echo "Run 'python3 -m flake8 src/ --max-line-length=88' to verify"
