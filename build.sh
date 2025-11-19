#!/bin/bash

# Build and install Ghidra plugin script

# Configuration
GHIDRA_DIR="$HOME/xtra/linux/Ohjelmat/ghidra_11.4.2_PUBLIC"
PLUGIN_NAME="GhidraTCPCommentingPlugin"
PLUGIN_DIR="$GHIDRA_DIR/Ghidra/Extensions/$PLUGIN_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building and installing $PLUGIN_NAME...${NC}"

# Check if Gradle is available
if ! command -v gradle &> /dev/null; then
    echo -e "${RED}Error: Gradle is not installed or not in PATH${NC}"
    exit 1
fi

# Check if Ghidra directory exists
if [ ! -d "$GHIDRA_DIR" ]; then
    echo -e "${RED}Error: Ghidra directory does not exist: $GHIDRA_DIR${NC}"
    exit 1
fi

# Build the plugin
echo -e "${YELLOW}Building the plugin...${NC}"
if ./gradlew build -Pghidra.install.dir="$GHIDRA_DIR"; then
    echo -e "${GREEN}Plugin built successfully!${NC}"
else
    echo -e "${RED}Error: Failed to build plugin${NC}"
    exit 1
fi

# Create plugin directory if it doesn't exist
mkdir -p "$PLUGIN_DIR"

# Copy the built plugin to Ghidra's Extensions directory
echo -e "${YELLOW}Installing plugin to Ghidra...${NC}"
cp -r dist/* "$PLUGIN_DIR/" 2>/dev/null || echo "No dist directory found, copying JAR files"

# Copy JAR files from build/libs if they exist
if [ -d "build/libs" ]; then
    cp build/libs/*.jar "$PLUGIN_DIR/"
    echo -e "${GREEN}JAR files copied to $PLUGIN_DIR${NC}"
else
    echo -e "${YELLOW}No JAR files found in build/libs${NC}"
fi

# Copy any dependencies if they exist
if [ -d "lib" ]; then
    cp -r lib/* "$PLUGIN_DIR/" 2>/dev/null || echo "No lib directory or it's empty"
fi

# Copy configuration files
cp -r lib "$PLUGIN_DIR/" 2>/dev/null || echo "No lib directory to copy"

echo -e "${GREEN}Plugin installed successfully!${NC}"
echo -e "${GREEN}Plugin location: $PLUGIN_DIR${NC}"
echo -e "${YELLOW}Please restart Ghidra to load the new plugin.${NC}"

# Check if Ghidra is currently running and warn the user
if pgrep -f "ghidra.*.jar" > /dev/null; then
    echo -e "${YELLOW}Warning: Ghidra appears to be running. Please restart Ghidra to load the new plugin.${NC}"
fi