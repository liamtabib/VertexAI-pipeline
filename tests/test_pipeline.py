#!/usr/bin/env python3
"""
Test script to verify the complete ecommerce analytics pipeline
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Test the complete pipeline"""
    base_dir = Path(__file__).parent
    dbt_dir = base_dir / "transform" / "ecommerce_metrics"
    dashboard_dir = base_dir / "dashboard"
    
    # Set environment variables
    env = os.environ.copy()
    env['GCP_PROJECT'] = 'pipeline-466508'
    env['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/liamtabibzadeh/Documents/hobby/env_files/pipeline-466508-86be2f5fd346.json'
    
    print("🚀 TESTING ECOMMERCE ANALYTICS PIPELINE")
    print(f"Base directory: {base_dir}")
    
    # Test 1: dbt debug
    print("\n" + "="*60)
    print("TEST 1: dbt connection")
    result = subprocess.run(
        ["dbt", "debug", "--profiles-dir", "."],
        cwd=dbt_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ dbt connection successful")
    else:
        print("❌ dbt connection failed")
        print(result.stderr)
        return False
    
    # Test 2: dbt run
    print("\n" + "="*60)
    print("TEST 2: dbt models")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd=dbt_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ dbt models built successfully")
        print(f"Models completed: {result.stdout.count('OK created')}")
    else:
        print("❌ dbt models failed")
        print(result.stderr)
        return False
    
    # Test 3: DuckDB export
    print("\n" + "="*60)
    print("TEST 3: DuckDB export")
    result = subprocess.run(
        ["python", "export_to_duckdb.py"],
        cwd=base_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ DuckDB export successful")
        print(f"Tables exported: {result.stdout.count('Successfully exported')}")
    else:
        print("❌ DuckDB export failed")
        print(result.stderr)
        return False
    
    # Test 4: Evidence sources
    print("\n" + "="*60)
    print("TEST 4: Evidence sources")
    result = subprocess.run(
        ["npm", "run", "sources"],
        cwd=dashboard_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Evidence sources processed successfully")
        print(f"Tables processed: {result.stdout.count('Finished')}")
    else:
        print("❌ Evidence sources failed")
        print(result.stderr)
        return False
    
    # Test 5: Evidence build
    print("\n" + "="*60)
    print("TEST 5: Evidence build")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=dashboard_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Evidence dashboard built successfully")
    else:
        print("❌ Evidence build failed")
        print(result.stderr)
        return False
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("The complete ecommerce analytics pipeline is working correctly.")
    print("\nTo run the pipeline:")
    print("1. dbt: cd transform/ecommerce_metrics && dbt run --profiles-dir .")
    print("2. Export: python export_to_duckdb.py")
    print("3. Dashboard: cd dashboard && npm run dev")
    print("4. Orchestration: dagster dev")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)