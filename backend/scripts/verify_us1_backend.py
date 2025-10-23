#!/usr/bin/env python3
"""
US1 Backend Verification Script

This script verifies that the US1 backend implementation is complete
by checking that the required methods and endpoints exist with the correct signatures.
"""

import ast
import sys
from pathlib import Path


def check_tool_service():
    """Verify ToolService has the required US1 methods."""
    print("Checking ToolService implementation...")
    
    service_file = Path(__file__).parent.parent / "src" / "services" / "tool_service.py"
    
    with open(service_file) as f:
        tree = ast.parse(f.read())
    
    # Find the ToolService class
    tool_service_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ToolService":
            tool_service_class = node
            break
    
    if not tool_service_class:
        print("  ❌ ToolService class not found")
        return False
    
    # Check for list_tools method
    list_tools_method = None
    count_tools_method = None
    
    for item in tool_service_class.body:
        if isinstance(item, ast.AsyncFunctionDef):
            if item.name == "list_tools":
                list_tools_method = item
            elif item.name == "count_tools":
                count_tools_method = item
    
    if not list_tools_method:
        print("  ❌ list_tools method not found")
        return False
    
    # Check list_tools has required parameters
    list_tools_params = [arg.arg for arg in list_tools_method.args.args]
    required_params = ["self", "page", "limit", "search", "status", "categories", "vendor", "sort_by", "sort_order"]
    
    for param in required_params:
        if param not in list_tools_params:
            print(f"  ❌ list_tools missing parameter: {param}")
            return False
    
    print("  ✅ list_tools method has all required parameters")
    
    if not count_tools_method:
        print("  ❌ count_tools method not found")
        return False
    
    print("  ✅ count_tools method found")
    
    return True


def check_admin_api():
    """Verify admin API has the required US1 endpoints."""
    print("\nChecking Admin API endpoints...")
    
    admin_file = Path(__file__).parent.parent / "src" / "api" / "admin.py"
    
    with open(admin_file) as f:
        content = f.read()
    
    # Check for GET /admin/tools endpoint
    if '@router.get("/tools")' not in content:
        print("  ❌ GET /tools endpoint not found")
        return False
    
    print("  ✅ GET /tools endpoint found")
    
    # Parse and check the endpoint function
    tree = ast.parse(content)
    
    list_tools_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_tools":
            list_tools_func = node
            break
    
    if not list_tools_func:
        print("  ❌ list_tools function not found")
        return False
    
    # Check for query parameters
    list_tools_params = [arg.arg for arg in list_tools_func.args.args]
    required_query_params = ["page", "limit", "search", "status", "category", "vendor", "sort_by", "sort_order"]
    
    for param in required_query_params:
        if param not in list_tools_params:
            print(f"  ❌ list_tools missing query parameter: {param}")
            return False
    
    print("  ✅ All query parameters present")
    
    # Check the endpoint returns pagination metadata
    if "total_pages" not in content or "has_next" not in content or "has_prev" not in content:
        print("  ❌ Pagination metadata (total_pages, has_next, has_prev) not found in response")
        return False
    
    print("  ✅ Pagination metadata included")
    
    # Check for filters_applied metadata
    if "filters_applied" not in content:
        print("  ❌ filters_applied metadata not found in response")
        return False
    
    print("  ✅ filters_applied metadata included")
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("US1 Backend Implementation Verification")
    print("=" * 60)
    
    service_ok = check_tool_service()
    api_ok = check_admin_api()
    
    print("\n" + "=" * 60)
    if service_ok and api_ok:
        print("✅ US1 Backend Implementation VERIFIED")
        print("\nAll required features are implemented:")
        print("  - Enhanced list_tools() service method with filtering")
        print("  - Enhanced GET /admin/tools API endpoint")
        print("  - Pagination metadata (total_pages, has_next, has_prev)")
        print("  - filters_applied metadata object")
        print("\nBackend is ready for integration testing.")
        return 0
    else:
        print("❌ US1 Backend Implementation INCOMPLETE")
        print("\nPlease review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
