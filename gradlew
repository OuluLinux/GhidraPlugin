#!/bin/sh

#
# Copyright © 2015-2021 The Gradle Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
DEFAULT_JVM_OPTS="-Xmx64m -Xms64m"

# Use the maximum available, or set MAX_FD != -1 to use that value.
MAX_FD="maximum"

warn () {
    echo >&2 "$*"
}

die () {
    echo >&2
    echo >&2 "$*"
    echo >&2
    exit 1
}

# OS specific support (must be 'true' or 'false').
cygwin=false
msys=false
darwin=false
case "$(uname)" in
  CYGWIN* )
    cygwin=true
    ;;
  Darwin* )
    darwin=true
    ;;
  MINGW* )
    msys=true
    ;;
esac

# For Cygwin or MSYS, switch paths to Windows format before running java
if $cygwin || $msys ; then
    [ -n "$JAVA_HOME" ] && JAVA_HOME=$(cygpath --path --windows "$JAVA_HOME")
    [ -n "$CLASSPATH" ] && CLASSPATH=$(cygpath --path --windows "$CLASSPATH")
    [ -n "$GRADLE_HOME" ] && GRADLE_HOME=$(cygpath --path --windows "$GRADLE_HOME")
    [ -n "$GRADLE_OPTS" ] && GRADLE_OPTS=$(cygpath --path --windows "$GRADLE_OPTS")
    [ -n "$JAVA_OPTS" ] && JAVA_OPTS=$(cygpath --path --windows "$JAVA_OPTS")
fi

# Attempt to set APP_HOME

# Resolve links: $0 may be a link
app_path=$0

# Need this for daisy-chained symlinks.
while
    APP_HOME="${app_path%/*}"
    [ -h "$app_path" ]
do
    ls=$( ls -ld "$app_path" )
    link="${ls#*' -> '}"
    case $link in             #(
      /*)   app_path="$link" ;; #(
      *)    app_path="$APP_HOME/$link" ;;
    esac
done

# This is normally unused
# shellcheck disable=SC2034
APP_BASE_NAME="${0##*/}"
# Discard cd standard output in case $CDPATH is set (https://github.com/gradle/gradle/issues/25038)
APP_HOME=$( cd "${APP_HOME:-./}" > /dev/null && pwd -P ) || die "Failed to determine Gradle wrapper script location"

# Use the maximum available, or set MAX_FD != -1 to use that value.
MAX_FD=${MAX_FD:-maximum}

warn () {
    echo >&2 "$*"
}

die () {
    echo >&2
    echo >&2 "$*"
    echo >&2
    exit 1
}

# OS specific support (must be 'true' or 'false').
cygwin=false
msys=false
darwin=false
nonstop=false
case "$(uname)" in
  CYGWIN* )
    cygwin=true
    ;;
  Darwin* )
    darwin=true
    ;;
  MINGW* )
    msys=true
    ;;
  NONSTOP* )
    nonstop=true
    ;;
esac

CLASSPATH=$APP_HOME/gradle/wrapper/gradle-wrapper.jar


# Determine the Java command to use to start the JVM.
if [ -n "$JAVA_HOME" ] ; then
    if [ -x "$JAVA_HOME/jre/sh/java" ] ; then
        # IBM's JDK on AIX uses strange locations for the executables
        JAVACMD=$JAVA_HOME/jre/sh/java
    else
        JAVACMD=$JAVA_HOME/bin/java
    fi
    if [ ! -x "$JAVACMD" ] ; then
        die "ERROR: JAVA_HOME is set to an invalid directory: $JAVA_HOME

Please set the JAVA_HOME variable in your environment to match the
location of your Java installation."
    fi
else
    JAVACMD=java
    which java >/dev/null 2>&1 || die "ERROR: JAVA_HOME is set to an invalid directory: $JAVA_HOME

Please set the JAVA_HOME variable in your environment to match the
location of your Java installation."
fi

# Increase the maximum file descriptors if we can.
if ! "$cygwin" && ! "$darwin" && ! "$nonstop" ; then
    case $MAX_FD in
      max*)
        # In POSIX sh, ulimit -H is undefined. That's why the result is checked to see if it worked.
        # shellcheck disable=SC2039,SC3028
        MAX_FD=$( ulimit -H -n ) ||
            warn "Could not query maximum file descriptor limit"
    esac
    case $MAX_FD in
      '' | soft ) :;; # leave $MAX_FD as existing value
      *)
        # In POSIX sh, ulimit -n is undefined. That's why the result is checked to see if it worked.
        # shellcheck disable=SC2039,SC3028
        ulimit -n "$MAX_FD" ||
            warn "Could not set maximum file descriptor limit to $MAX_FD"
    esac
fi

# Collect all arguments for the java command, stacking in reverse order:
#   * args from the command line
#   * the main class name
#   * -classpath
#   * -D...appname settings
#   * --module-path (only if needed)
#   * DEFAULT_JVM_OPTS, JAVA_OPTS, and GRADLE_OPTS environment variables.

# For Cygwin or MSYS, switch paths to Windows format before running java
if $cygwin || $msys ; then
    APP_HOME=$(cygpath --path --windows "$APP_HOME")
    CLASSPATH=$(cygpath --path --windows "$CLASSPATH")
    
    JAVACMD=$(which "$JAVACMD" 2>/dev/null)
    [ -n "$JAVACMD" ] || die "ERROR: JAVA_HOME is set to an invalid directory: $JAVA_HOME"
fi

# Collect all arguments for the java command:
set -f # disable globbing
args=""
add_arg() {
    if [ -z "$args" ]; then
        args="$1"
    else
        args="$args '$1'"
    fi
}

# Use "x" prefix to test for empty
if [ "x$DEFAULT_JVM_OPTS" != "x" ] ; then
    for jvm_opt in $DEFAULT_JVM_OPTS; do
        add_arg "$jvm_opt"
    done
fi

if [ "x$JAVA_OPTS" != "x" ] ; then
    for opt in $JAVA_OPTS; do
        add_arg "$opt"
    done
fi

if [ "x$GRADLE_OPTS" != "x" ] ; then
    for opt in $GRADLE_OPTS; do
        add_arg "$opt"
    done
fi

add_arg "-Dorg.gradle.appname=$APP_BASE_NAME"

# Check if Gradle is being run from a terminal
if [ -t 0 ] && [ -t 1 ]; then
    add_arg "-Dorg.gradle.daemon.idletimeout=10800000"
fi

add_arg "-classpath" "$CLASSPATH"
add_arg "org.gradle.wrapper.GradleWrapperMain"
set +f # re-enable globbing

# Check if gradle-local.properties exists and source ghidra.install.dir if it does
gradle_properties=""
if [ -f "gradle-local.properties" ]; then
    ghidra_dir=$(grep "ghidra.install.dir" gradle-local.properties | cut -d'=' -f2-)
    if [ -n "$ghidra_dir" ]; then
        gradle_properties="-Pghidra.install.dir=$ghidra_dir"
    fi
fi

# Parse gradle-local.properties to get ghidra.install.dir if it exists
GHIDRA_INSTALL_DIR=""
if [ -f "gradle-local.properties" ]; then
    GHIDRA_INSTALL_DIR=$(grep "ghidra.install.dir" gradle-local.properties | cut -d'=' -f2-)
fi

# Build the command
JAVA_OPTS_CMD=""
if [ -n "$JAVA_OPTS" ]; then
    JAVA_OPTS_CMD="$JAVA_OPTS"
fi

GRADLE_OPTS_CMD=""
if [ -n "$GRADLE_OPTS" ]; then
    GRADLE_OPTS_CMD="$GRADLE_OPTS"
fi

# Build the java command arguments
CMD_ARGS=""
if [ "x$DEFAULT_JVM_OPTS" != "x" ]; then
    CMD_ARGS="$DEFAULT_JVM_OPTS"
fi

if [ -n "$JAVA_OPTS_CMD" ]; then
    if [ -n "$CMD_ARGS" ]; then
        CMD_ARGS="$CMD_ARGS $JAVA_OPTS_CMD"
    else
        CMD_ARGS="$JAVA_OPTS_CMD"
    fi
fi

if [ -n "$GRADLE_OPTS_CMD" ]; then
    if [ -n "$CMD_ARGS" ]; then
        CMD_ARGS="$CMD_ARGS $GRADLE_OPTS_CMD"
    else
        CMD_ARGS="$GRADLE_OPTS_CMD"
    fi
fi

# Execute the java command
if [ -n "$GHIDRA_INSTALL_DIR" ]; then
    exec "$JAVACMD" $CMD_ARGS -Dorg.gradle.appname="$APP_BASE_NAME" -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@" -Pghidra.install.dir="$GHIDRA_INSTALL_DIR"
else
    exec "$JAVACMD" $CMD_ARGS -Dorg.gradle.appname="$APP_BASE_NAME" -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
fi