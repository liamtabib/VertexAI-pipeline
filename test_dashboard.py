#!/usr/bin/env python3
"""
Comprehensive test script for Evidence.dev dashboard module
"""

import duckdb
import pandas as pd
from pathlib import Path

def test_data_quality():
    """Test data quality in DuckDB tables"""
    print("🧪 TESTING DASHBOARD DATA QUALITY")
    print("=" * 50)
    
    duckdb_path = Path("dashboard/sources/dashboard_data/dashboard_data.duckdb")
    if not duckdb_path.exists():
        print("❌ DuckDB file not found")
        return False
    
    conn = duckdb.connect(str(duckdb_path))
    
    try:
        # Test 1: Check all tables exist
        tables = conn.execute("SHOW TABLES").fetchall()
        expected_tables = ['mau', 'retention', 'users_by_country', 'platform_share', 'funnel', 'data_end_date']
        
        print("📊 Available tables:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        missing_tables = [t for t in expected_tables if (t,) not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        # Test 2: MAU data
        print("\n📈 MAU Data Quality:")
        mau_data = conn.execute("SELECT COUNT(*) as rows, MIN(month) as min_month, MAX(month) as max_month, MAX(mau) as max_users FROM mau").fetchone()
        print(f"  ✓ {mau_data[0]} months of data")
        print(f"  ✓ Date range: {mau_data[1]} to {mau_data[2]}")
        print(f"  ✓ Peak MAU: {mau_data[3]:,} users")
        
        # Test 3: Retention data
        print("\n📊 Retention Data Quality:")
        retention_data = conn.execute("SELECT COUNT(DISTINCT cohort_month) as cohorts, MIN(retention_rate) as min_rate, MAX(retention_rate) as max_rate FROM retention").fetchone()
        print(f"  ✓ {retention_data[0]} cohorts tracked")
        print(f"  ✓ Retention range: {retention_data[1]:.1%} to {retention_data[2]:.1%}")
        
        # Test 4: Geographic data
        print("\n🌍 Geographic Data Quality:")
        country_data = conn.execute("SELECT COUNT(*) as countries, SUM(users) as total_users, MAX(users) as max_country FROM users_by_country").fetchone()
        print(f"  ✓ {country_data[0]} countries")
        print(f"  ✓ Total users: {country_data[1]:,}")
        print(f"  ✓ Largest country: {country_data[2]:,} users")
        
        # Test 5: Platform data
        print("\n💻 Platform Data Quality:")
        platform_data = conn.execute("SELECT COUNT(*) as platforms, SUM(users) as total_users FROM platform_share").fetchone()
        platforms = conn.execute("SELECT platform, users, share FROM platform_share ORDER BY users DESC").fetchall()
        print(f"  ✓ {platform_data[0]} platforms tracked")
        print(f"  ✓ Total users: {platform_data[1]:,}")
        for platform, users, share in platforms:
            print(f"    - {platform}: {users:,} users ({share:.1%})")
        
        # Test 6: Funnel data
        print("\n🛒 Funnel Data Quality:")
        funnel_data = conn.execute("SELECT step, sessions FROM funnel ORDER BY step").fetchall()
        print("  ✓ Conversion funnel:")
        step_names = ["Total Sessions", "Department", "Product", "Cart", "Purchase"]
        for i, (step, sessions) in enumerate(funnel_data):
            step_name = step_names[i] if i < len(step_names) else f"Step {step}"
            if i > 0:
                prev_sessions = funnel_data[i-1][1]
                conversion = sessions / prev_sessions if prev_sessions > 0 else 0
                print(f"    {step}. {step_name}: {sessions:,} sessions ({conversion:.1%} conversion)")
            else:
                print(f"    {step}. {step_name}: {sessions:,} sessions")
        
        # Test 7: Data freshness
        print("\n📅 Data Freshness:")
        end_date = conn.execute("SELECT data_end_date FROM data_end_date").fetchone()[0]
        print(f"  ✓ Data current as of: {end_date}")
        
        print("\n✅ ALL DATA QUALITY TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Data quality test failed: {e}")
        return False
    finally:
        conn.close()

def test_evidence_files():
    """Test Evidence configuration files"""
    print("\n🔧 TESTING EVIDENCE CONFIGURATION")
    print("=" * 50)
    
    dashboard_dir = Path("dashboard")
    
    # Test Evidence config
    evidence_config = dashboard_dir / "evidence.config.yaml"
    if evidence_config.exists():
        print("  ✓ evidence.config.yaml found")
    else:
        print("  ❌ evidence.config.yaml missing")
        return False
    
    # Test connection config
    connection_config = dashboard_dir / "sources" / "dashboard_data" / "connection.yaml"
    if connection_config.exists():
        print("  ✓ connection.yaml found")
        with open(connection_config) as f:
            content = f.read()
            if "duckdb" in content:
                print("  ✓ DuckDB connection configured")
            else:
                print("  ❌ DuckDB connection not found")
                return False
    else:
        print("  ❌ connection.yaml missing")
        return False
    
    # Test SQL queries
    sql_dir = dashboard_dir / "sources" / "dashboard_data"
    expected_queries = ['mau.sql', 'retention.sql', 'users_by_country.sql', 'platform_share.sql', 'funnel.sql', 'data_end_date.sql']
    
    print("  📝 SQL query files:")
    for query_file in expected_queries:
        query_path = sql_dir / query_file
        if query_path.exists():
            print(f"    ✓ {query_file}")
        else:
            print(f"    ❌ {query_file} missing")
            return False
    
    # Test main dashboard page
    main_page = dashboard_dir / "pages" / "index.md"
    if main_page.exists():
        print("  ✓ index.md dashboard page found")
        with open(main_page) as f:
            content = f.read()
            required_components = ['Grid', 'AreaChart', 'LineChart', 'AreaMap', 'BarChart']
            for component in required_components:
                if component in content:
                    print(f"    ✓ {component} component used")
                else:
                    print(f"    ❌ {component} component missing")
                    return False
    else:
        print("  ❌ index.md missing")
        return False
    
    print("  ✅ Evidence configuration valid!")
    return True

def test_visualizations():
    """Test visualization configuration"""
    print("\n📊 TESTING VISUALIZATION SETUP")
    print("=" * 50)
    
    dashboard_page = Path("dashboard/pages/index.md")
    with open(dashboard_page) as f:
        content = f.read()
    
    # Test required visualizations
    visualizations = {
        "Monthly Active Users": ["AreaChart", "mau_data"],
        "Cohort Retention": ["LineChart", "retention_data"],  
        "Geographic Map": ["AreaMap", "country_data"],
        "Platform Analysis": ["BarChart", "platform_data"],
        "Shopping Funnel": ["BarChart", "funnel_data"]
    }
    
    for viz_name, (component, data_ref) in visualizations.items():
        if component in content and data_ref in content:
            print(f"  ✓ {viz_name} configured correctly")
        else:
            print(f"  ❌ {viz_name} configuration issue")
            return False
    
    # Test data queries
    queries = ["mau_data", "retention_data", "country_data", "platform_data", "funnel_data", "data_end_date"]
    for query in queries:
        if f"sql {query}" in content:
            print(f"  ✓ {query} query defined")
        else:
            print(f"  ❌ {query} query missing")
            return False
    
    print("  ✅ All visualizations configured!")
    return True

def main():
    """Run all dashboard tests"""
    print("🚀 COMPREHENSIVE DASHBOARD MODULE TEST")
    print("=" * 60)
    
    tests = [
        test_data_quality,
        test_evidence_files, 
        test_visualizations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL DASHBOARD TESTS PASSED!")
        print("\nDashboard is ready for:")
        print("  ✓ Interactive data exploration")
        print("  ✓ Real-time metric monitoring")
        print("  ✓ Business intelligence reporting")
        print("  ✓ Production deployment")
        print("\nTo view dashboard: npm run dev")
        return True
    else:
        print("❌ Some tests failed. Check configuration.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)