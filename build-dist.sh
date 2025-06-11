#!/bin/bash

# Build distribution package
# Creates a clean distributable archive with wheel and install scripts

set -e

echo "🔨 Building Sagemcom MCP distribution..."

# Clean previous builds
rm -rf dist/ build/ sagemcom-mcp-*.tar.gz

# Build the package
echo "📦 Building wheel..."
uv build

# Verify build succeeded
WHEEL_FILE=$(find dist/ -name "*.whl" | head -1)
if [[ -z "$WHEEL_FILE" ]]; then
    echo "❌ Build failed - no wheel file created"
    exit 1
fi

# Remove sdist to avoid confusion (we only want wheel + custom archive)
rm -f dist/*.tar.gz

echo "✅ Built: $WHEEL_FILE"

# Get version from pyproject.toml
VERSION=$(grep "^version" pyproject.toml | sed 's/version = "\(.*\)"/\1/')
PACKAGE_NAME=$(grep "^name" pyproject.toml | sed 's/name = "\(.*\)"/\1/')
DIST_DIR_NAME="${PACKAGE_NAME}-${VERSION}"
DIST_ARCHIVE="${DIST_DIR_NAME}.tar.gz"

echo "📦 Creating distribution archive: ${DIST_ARCHIVE}"

# Create temporary directory for clean packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${DIST_DIR_NAME}"
mkdir -p "$PACKAGE_DIR"

# Copy only the wheel file (not the sdist)
cp "$WHEEL_FILE" "$PACKAGE_DIR/"

# Copy install scripts with clean names
cp install-mcp-dist.sh "$PACKAGE_DIR/install-mcp.sh"
cp install-cli-dist.sh "$PACKAGE_DIR/install-cli.sh"
cp uninstall.sh "$PACKAGE_DIR/uninstall.sh"
cp INSTALLER_README.md "$PACKAGE_DIR/README.md"

# Copy installer app if it exists
if [ -d "run_installer.app" ]; then
    cp -R "run_installer.app" "$PACKAGE_DIR/"
    echo "✅ Added GUI installer app"
fi

# Create the final archive
echo "📦 Creating archive..."
(cd "$TEMP_DIR" && tar -czf "$DIST_ARCHIVE" "$DIST_DIR_NAME")

# Move archive to dist folder and clean up
mv "${TEMP_DIR}/${DIST_ARCHIVE}" "dist/"
rm -rf "$TEMP_DIR"

# Clean up redundant files in dist/ - only keep the final archive
rm -f dist/*.whl

echo ""
echo "🎉 Distribution ready!"
echo ""
echo "📄 Archive: dist/${DIST_ARCHIVE}"
echo ""
echo "📋 To install:"
echo "   tar -xvf ${DIST_ARCHIVE}"
echo "   cd ${DIST_DIR_NAME}"
echo "   ./install-mcp.sh  # Full installation"
echo "   ./install-cli.sh  # CLI only"
echo ""
echo "🖱️  On macOS: Double-click 'run_installer.app' for GUI installation"

