#!/bin/bash

# Build script for GhidraTCPCommentingPlugin

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building GhidraTCPCommentingPlugin...${NC}"

# Check if the source directory exists
if [ ! -d "./src/main/java" ]; then
    echo -e "${RED}Error: Source directory './src/main/java' does not exist${NC}"
    exit 1
fi

# Check if built Ghidra distribution exists
GHIDRA_BUILT_PATH="./ghidra-Ghidra_11.4.2_build/build/dist/ghidra_11.4.2_DEV"
if [ ! -d "$GHIDRA_BUILT_PATH" ]; then
    echo -e "${RED}Error: Built Ghidra distribution not found at $GHIDRA_BUILT_PATH${NC}"
    exit 1
fi

echo -e "${YELLOW}Setting up classpath with built Ghidra JARs...${NC}"

# Build the classpath with all required Ghidra JARs
CLASSPATH="."
for jar in $(find $GHIDRA_BUILT_PATH -name "*.jar" | grep -E "(Framework|SoftwareModeling|Base|Docking|GUI|DB|Generic|Utility|Project|FileSystem|Graph|Emulation|Help|Code|Decompiler|Program|Application|FlatLaf|Log4j|Commons|JDom|Jna|Bcprov|Guava|JGraphT|Jung|Jackson|Jettison|JCommander|JLine|JOpt|Jsch|Jython|Jzlib|Logback|Slf4j|Xalan|Xerces|XmlResolver|Annotations|ASM|Antlr|Apache|Google|Jsr|Hamcrest|Junit|Mockito|Objenesis|Bytebuddy|Javax|Jdk|Netty|Protobuf)") 
do
    CLASSPATH="$CLASSPATH:$jar"
done

echo -e "${YELLOW}Compiling Java source files...${NC}"

# Create the build directory
rm -rf build
mkdir -p build/classes

# Find all .java files
JAVA_FILES=$(find src/main/java -name "*.java")

if [ -z "$JAVA_FILES" ]; then
    echo -e "${RED}Error: No Java source files found${NC}"
    exit 1
fi

echo "Found Java files: $JAVA_FILES"

# Compile the Java files
if javac -cp "$CLASSPATH" -source 11 -target 11 -d build/classes $JAVA_FILES; then
    echo -e "${GREEN}Compilation successful!${NC}"
    
    # Create the JAR file
    cd build/classes
    jar cf ../GhidraTCPCommentingPlugin.jar .
    cd ../..

    echo -e "${GREEN}JAR file created at build/GhidraTCPCommentingPlugin.jar${NC}"
    
    # If Ghidra installation exists, install the plugin there
    GHIDRA_INSTALL_DIR="$HOME/xtra/linux/Ohjelmat/ghidra_11.4.2_PUBLIC"
    if [ -d "$GHIDRA_INSTALL_DIR/Ghidra/Extensions" ]; then
        PLUGIN_INSTALL_DIR="$GHIDRA_INSTALL_DIR/Ghidra/Extensions/GhidraTCPCommentingPlugin"
        mkdir -p "$PLUGIN_INSTALL_DIR"
        
        cp build/GhidraTCPCommentingPlugin.jar "$PLUGIN_INSTALL_DIR/"
        echo -e "${GREEN}Plugin installed to $PLUGIN_INSTALL_DIR${NC}"
        
        # Create a basic module info file
        cat > "$PLUGIN_INSTALL_DIR/GhidraModule.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<moduleMetadata>
    <moduleType>Extension</moduleType>
    <name>GhidraTCPCommentingPlugin</name>
    <version>1.0.0</version>
    <description>Provides TCP server functionality for client communication with Ghidra</description>
    <createdOn>2025-11-20</createdOn>
    <pluginClassNames>
        <className>GhidraTCPCommentingPlugin</className>
    </pluginClassNames>
</moduleMetadata>
EOF
        
        echo -e "${GREEN}Module metadata created at $PLUGIN_INSTALL_DIR/GhidraModule.xml${NC}"
    else
        echo -e "${YELLOW}Ghidra installation directory not found. Plugin JAR created but not installed.${NC}"
    fi

    echo -e "${GREEN}Build completed successfully!${NC}"
else
    echo -e "${RED}Compilation failed${NC}"
    echo -e "${YELLOW}Classpath used: $CLASSPATH${NC}"
    exit 1
fi