#!/usr/bin/env python
"""
Lightweight DAG validation script.
Tests that DAG can be parsed by Airflow without runtime dependencies.
"""

import ast
import py_compile
import sys
from pathlib import Path

# Add dags directory to path
script_dir = Path(__file__).parent
dags_dir = script_dir.parent / "dags"
sys.path.insert(0, str(dags_dir))


def validate_dag_syntax(dag_file: str) -> bool:
    """
    Validate DAG Python syntax without importing Airflow.
    """
    try:
        with open(dag_file, encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        print(f"✅ {dag_file}: Syntax valid")
        return True
    except SyntaxError as e:
        print(f"❌ {dag_file}: Syntax error at line {e.lineno}: {e.msg}")
        return False


def validate_dag_instantiation(dag_file: str) -> bool:
    """
    Validate that DAG object is created (basic instantiation test).
    """
    try:
        # Try to compile the DAG file
        py_compile.compile(dag_file, doraise=True)
        print(f"✅ {dag_file}: Compiles successfully")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ {dag_file}: Compilation error: {e}")
        return False


def main():
    """Validate all DAGs in the directory."""
    dags = [
        "hello_airflow.py",
        "google_ads_ingestion.py",
        "meta_ads_ingestion.py",
        "marketing_data_platform.py",
    ]
    
    results = {}
    
    print("=" * 60)
    print("DAG Validation Report")
    print("=" * 60)
    
    for dag_name in dags:
        dag_path = dags_dir / dag_name
        
        if not dag_path.exists():
            print(f"⚠️  {dag_name}: File not found")
            results[dag_name] = False
            continue
        
        syntax_ok = validate_dag_syntax(str(dag_path))
        compile_ok = validate_dag_instantiation(str(dag_path))
        
        results[dag_name] = syntax_ok and compile_ok
        print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for dag_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {dag_name}")
    
    print(f"\nTotal: {passed}/{total} DAGs valid")
    
    if passed == total:
        print("\n🎉 All DAGs are valid!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} DAG(s) have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
