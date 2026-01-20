#!/bin/bash
# dbt helper script for Media Data Platform

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DBT_DIR="dbt/mdp"

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}   Media Data Platform - dbt Helper   ${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

cd "$DBT_DIR"

case "$1" in
  parse)
    echo -e "${GREEN}→ Validating dbt models...${NC}"
    dbt parse
    ;;
  
  compile)
    echo -e "${GREEN}→ Compiling dbt models...${NC}"
    dbt compile --select "$2"
    ;;
  
  run)
    if [ -z "$2" ]; then
      echo -e "${GREEN}→ Running all dbt models...${NC}"
      dbt run
    else
      echo -e "${GREEN}→ Running dbt models: $2${NC}"
      dbt run --select "$2"
    fi
    ;;
  
  test)
    if [ -z "$2" ]; then
      echo -e "${GREEN}→ Testing all dbt models...${NC}"
      dbt test
    else
      echo -e "${GREEN}→ Testing dbt models: $2${NC}"
      dbt test --select "$2"
    fi
    ;;
  
  staging)
    echo -e "${GREEN}→ Running staging layer...${NC}"
    dbt run --select staging
    echo -e "${GREEN}→ Testing staging layer...${NC}"
    dbt test --select staging
    ;;
  
  docs)
    echo -e "${GREEN}→ Generating dbt documentation...${NC}"
    dbt docs generate
    echo -e "${GREEN}→ Serving documentation on http://localhost:8080${NC}"
    dbt docs serve --port 8080
    ;;
  
  deps)
    echo -e "${GREEN}→ Installing dbt dependencies...${NC}"
    dbt deps
    ;;
  
  clean)
    echo -e "${YELLOW}→ Cleaning dbt artifacts...${NC}"
    dbt clean
    ;;
  
  *)
    echo "Usage: $0 {parse|compile|run|test|staging|docs|deps|clean} [selector]"
    echo ""
    echo "Commands:"
    echo "  parse          Validate dbt project syntax"
    echo "  compile        Compile dbt models (optional: --select)"
    echo "  run [selector] Run dbt models (optional: --select)"
    echo "  test [selector] Test dbt models (optional: --select)"
    echo "  staging        Run and test staging layer"
    echo "  docs           Generate and serve documentation"
    echo "  deps           Install dbt packages"
    echo "  clean          Remove dbt artifacts"
    echo ""
    echo "Examples:"
    echo "  $0 parse"
    echo "  $0 run staging"
    echo "  $0 test staging.google_ads"
    echo "  $0 staging"
    exit 1
    ;;
esac

echo ""
echo -e "${GREEN}✓ Done!${NC}"
