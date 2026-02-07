#!/usr/bin/env python3
"""
LOCAL Testing Script - For Testing on Localhost
Run: python test_local.py
"""

import requests
import json
from datetime import datetime
import sys

# ============================================================
# CONFIGURATION - CHANGE THIS FOR LOCAL TESTING
# ============================================================
BASE_URL = "http://localhost:5000"  # Change port if different
# Common alternatives:
# BASE_URL = "http://localhost:8000"
# BASE_URL = "http://127.0.0.1:5000"

# ANSI colors for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{msg:^70}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")

def print_json(data, title="Response"):
    """Pretty print JSON data"""
    print(f"\n{CYAN}📄 {title}:{RESET}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()

# Global token storage
TOKEN = None

def check_server_running():
    """Check if local server is running"""
    print_header("CHECKING LOCAL SERVER")
    
    print_info(f"Testing connection to: {BASE_URL}")
    
    try:
        response = requests.get(BASE_URL, timeout=3)
        print_success(f"✓ Server is running! Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print_error("❌ Cannot connect to local server!")
        print_info("\n🔧 Is your Flask app running?")
        print_info("\nTo start your server:")
        print_info("  python app.py")
        print_info("  # or")
        print_info("  flask run")
        print_info("  # or")
        print_info("  python main.py")
        print_info("\n⚠️  Make sure the port matches (default: 5000)")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def discover_routes():
    """Try to find available routes"""
    print_header("DISCOVERING AVAILABLE ROUTES")
    
    test_routes = [
        "/",
        "/api",
        "/api/admin",
        "/api/admin/login",
        "/api/admin/builder/login",
        "/health",
        "/api/health"
    ]
    
    print_info("Scanning endpoints...\n")
    
    found_routes = []
    
    for route in test_routes:
        url = f"{BASE_URL}{route}"
        try:
            response = requests.get(url, timeout=2)
            status = response.status_code
            
            if status == 404:
                print(f"  ❌ {route:30} - Not found")
            elif status == 405:
                print(f"  ✅ {route:30} - Exists (needs POST)")
                found_routes.append(route)
            elif status == 401:
                print(f"  🔒 {route:30} - Exists (needs auth)")
                found_routes.append(route)
            elif status == 200:
                print(f"  ✅ {route:30} - OK")
                found_routes.append(route)
            else:
                print(f"  ❓ {route:30} - Status {status}")
                found_routes.append(route)
                
        except Exception as e:
            print(f"  💥 {route:30} - Timeout/Error")
    
    if found_routes:
        print_success(f"\nFound {len(found_routes)} working endpoint(s)!")
    else:
        print_warning("\n⚠️  No admin endpoints found")
        print_info("\nMake sure you've added to your app.py:")
        print_info("  from admin_routes import admin_bp")
        print_info("  app.register_blueprint(admin_bp)")
    
    return found_routes

def test_login():
    """Test login endpoint"""
    global TOKEN
    
    print_header("TEST: LOGIN")
    
    url = f"{BASE_URL}/api/admin/builder/login"
    payload = {
        "username": "skyline_admin",
        "password": "builder123"
    }
    
    print_info(f"POST {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print_error("❌ 404 - Admin routes not registered!")
            print_warning("\n⚠️  Fix needed in your app.py:")
            print_info("  from admin_routes import admin_bp")
            print_info("  app.register_blueprint(admin_bp)")
            return False
            
        elif response.status_code == 500:
            print_error("❌ 500 - Server error!")
            print_warning("\nCheck your Flask console for the error")
            try:
                error_data = response.json()
                print_json(error_data, "Error Details")
            except:
                print_error(response.text[:500])
            return False
            
        elif response.status_code == 401:
            print_error("❌ 401 - Invalid credentials")
            try:
                error_data = response.json()
                print_json(error_data)
            except:
                pass
            print_info("\nCheck:")
            print_info("  1. Builder exists in Supabase 'builders' table")
            print_info("  2. Username: skyline_admin")
            print_info("  3. Password hash matches")
            return False
            
        elif response.status_code == 200:
            data = response.json()
            print_json(data, "Success!")
            
            if data.get('success'):
                TOKEN = data.get('token')
                print_success("✓ Login successful!")
                print_info(f"Username: {data.get('username')}")
                print_info(f"User Type: {data.get('user_type')}")
                print_info(f"Client: {data.get('client_name')}")
                print_info(f"Company: {data.get('company_name')}")
                print_info(f"Property: {data.get('property_name')}")
                return True
            else:
                print_error(f"Login failed: {data.get('error')}")
                return False
        else:
            print_error(f"Unexpected status: {response.status_code}")
            print_error(response.text[:300])
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection refused - is the server running?")
        return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard():
    """Test dashboard endpoint"""
    print_header("TEST: DASHBOARD")
    
    if not TOKEN:
        print_error("No token - login first")
        return False
    
    url = f"{BASE_URL}/api/admin/dashboard"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print_info(f"GET {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_json(data)
            
            if data.get('success'):
                print_success("✓ Dashboard loaded!")
                properties = data.get('properties', [])
                print_info(f"Properties: {len(properties)}")
                
                for prop in properties:
                    print(f"\n  📊 {prop.get('name')}")
                    print(f"     Leads: {prop.get('leads')}")
                    print(f"     Type: {prop.get('type')}")
                
                return True, properties
        
        print_error(f"Failed: {response.status_code}")
        return False, []
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False, []

def test_property_leads():
    """Test property leads endpoint"""
    print_header("TEST: PROPERTY LEADS")
    
    if not TOKEN:
        print_error("No token - login first")
        return False, []
    
    url = f"{BASE_URL}/api/admin/property/skyline/leads"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print_info(f"GET {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_json(data)
            
            if data.get('success'):
                leads = data.get('leads', [])
                print_success(f"✓ Found {len(leads)} lead(s)!")
                
                if leads:
                    print_info("\n👥 Leads:")
                    for i, lead in enumerate(leads[:5], 1):
                        print(f"\n  {i}. {lead.get('name')}")
                        print(f"     Email: {lead.get('email')}")
                        print(f"     Phone: {lead.get('phone')}")
                        print(f"     Generations: {lead.get('total_generations')}")
                else:
                    print_warning("  No leads in database yet")
                    print_info("  This is normal for a new setup")
                
                return True, leads
        
        print_error(f"Failed: {response.status_code}")
        return False, []
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False, []

def test_analytics():
    """Test analytics endpoint"""
    print_header("TEST: ANALYTICS")
    
    if not TOKEN:
        print_error("No token - login first")
        return False
    
    url = f"{BASE_URL}/api/admin/analytics"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print_info(f"GET {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_json(data)
            
            if data.get('success'):
                analytics = data.get('analytics', {})
                print_success("✓ Analytics loaded!")
                print(f"\n  📊 Statistics:")
                print(f"     Total Leads: {analytics.get('total_leads')}")
                print(f"     Total Generations: {analytics.get('total_generations')}")
                print(f"     Today's Leads: {analytics.get('today_leads')}")
                print(f"     Today's Generations: {analytics.get('today_generations')}")
                return True
        
        print_error(f"Failed: {response.status_code}")
        return False
        
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Run all local tests"""
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{CYAN}{'🏠 LOCAL API TESTING 🏠':^70}{RESET}")
    print(f"{CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^70}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    print_info(f"Testing against: {BASE_URL}")
    print_info("Make sure your Flask app is running!\n")
    
    results = []
    
    # Check server
    if not check_server_running():
        print_header("❌ SERVER NOT RUNNING")
        print_info("\nStart your Flask server first:")
        print_info("  cd C:\\interior-backend")
        print_info("  python app.py")
        print_info("\nThen run this test again.")
        return
    
    # Discover routes
    routes = discover_routes()
    
    # Test login
    if test_login():
        results.append(("Login", True))
        
        # Test dashboard
        success, _ = test_dashboard()
        results.append(("Dashboard", success))
        
        # Test property leads
        success, leads = test_property_leads()
        results.append(("Property Leads", success))
        
        # Test analytics
        success = test_analytics()
        results.append(("Analytics", success))
        
    else:
        results.append(("Login", False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"  {test_name:.<50} {status}")
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"  {GREEN}Passed: {passed}{RESET}  |  {RED}Failed: {failed}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    # Advice
    if passed == len(results):
        print_success("🎉 ALL TESTS PASSED!")
        print_info("\nYour local API is working perfectly!")
        print_info("Ready to deploy to Railway when you're ready.")
    elif results and not results[0][1]:
        print_warning("⚠️  ADMIN ROUTES NOT FOUND")
        print_info("\nAdd to your app.py:")
        print_info("  from admin_routes import admin_bp")
        print_info("  app.register_blueprint(admin_bp)")
        print_info("\nThen restart your Flask server.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  Interrupted{RESET}\n")
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()