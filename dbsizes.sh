#!/bin/bash
# Display mysql database sizes with total
# Requirements: mysql-client
# Author: John McNally, jmcnally@acm.org, 2/2/2023

RESULT=$(mysql -e 'SELECT table_schema, \
  ROUND(SUM(data_length + index_length) / 1024 / 1024, 0) \
  FROM information_schema.tables \
  GROUP BY table_schema;')

if [[ $? -ne 0 ]]; then
  echo "ERROR: mysql query failed"
  exit 1
fi

TOTAL=0

echo -e "Size (MB)  Name"

while IFS=$'\t' read -r NAME SIZE; do
  printf "%'8d   %s\n" "$SIZE" "$NAME"
  TOTAL=$(( TOTAL + SIZE ))
done <<< $(echo "$RESULT" | tail -n +2)

echo "-----------------------------"
printf "%'8d   %s\n" "$TOTAL" 'TOTAL'
