#!/bin/bash
# Simple License Mock Tool - No dependencies required
# Chỉ cần Python3 chuẩn, không cần cài thêm gì

PANEL_PATH="/www/server/panel"
SCRIPT_NAME="simple_license_mock.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_requirements() {
    # Check if we're in the right directory
    if [[ ! -f "$PANEL_PATH/$SCRIPT_NAME" ]]; then
        print_error "Script not found at $PANEL_PATH/$SCRIPT_NAME"
        return 1
    fi
    
    # Check Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is required but not installed"
        return 1
    fi
    
    # Check if we can write to panel directory
    if [[ ! -w "$PANEL_PATH" ]]; then
        print_error "No write permission to $PANEL_PATH. Run as root or with sudo."
        return 1
    fi
    
    return 0
}

show_help() {
    echo "Simple License Mock Tool for BT-Panel"
    echo "======================================"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  enable        Apply mock PRO license"
    echo "  disable       Remove mock license and restore original"
    echo "  status        Check current mock status"
    echo "  test          Test license functions"
    echo "  help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 enable     # Enable PRO mock"
    echo "  $0 status     # Check status"
    echo "  $0 disable    # Disable mock"
    echo ""
    echo "Note: This tool only uses Python3 standard library"
    echo "      No additional packages required!"
}

enable_mock() {
    print_status "Enabling mock PRO license..."
    
    cd "$PANEL_PATH" || exit 1
    
    if python3 "$SCRIPT_NAME" apply; then
        print_success "Mock PRO license enabled!"
        print_status "You can now test PRO features in BT-Panel"
        print_warning "Remember: This is for debugging only!"
    else
        print_error "Failed to enable mock license"
        return 1
    fi
}

disable_mock() {
    print_status "Disabling mock license..."
    
    cd "$PANEL_PATH" || exit 1
    
    if python3 "$SCRIPT_NAME" remove; then
        print_success "Mock license disabled and original restored!"
    else
        print_error "Failed to disable mock license"
        return 1
    fi
}

show_status() {
    print_status "Checking mock license status..."
    
    cd "$PANEL_PATH" || exit 1
    python3 "$SCRIPT_NAME" status
}

test_license() {
    print_status "Testing license functions..."
    
    cd "$PANEL_PATH" || exit 1
    
    # Test basic Python import
    python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, './class')

print('Testing imports...')

try:
    import os, json, time
    print('✓ Standard libraries OK')
except Exception as e:
    print(f'✗ Standard libraries failed: {e}')

# Test mock script
try:
    exec(open('simple_license_mock.py').read())
    print('✓ Mock script syntax OK')
except Exception as e:
    print(f'✗ Mock script error: {e}')

# Test file access
try:
    data_path = '/www/server/panel/data'
    if os.access(data_path, os.W_OK):
        print('✓ Data directory writable')
    else:
        print('✗ Data directory not writable')
except Exception as e:
    print(f'✗ File access test failed: {e}')
"
}

main() {
    case "$1" in
        "enable")
            check_requirements && enable_mock
            ;;
        "disable")
            check_requirements && disable_mock
            ;;
        "status")
            check_requirements && show_status
            ;;
        "test")
            check_requirements && test_license
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
