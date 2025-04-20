#!/bin/bash

set -euo pipefail

# Директории, в которых лежат альтернативные копии проекта
DIRS=("meetping_final" "meetping_rebuild_stage3" "meetping_rebuild_stage4" "meetpingpp")

echo "🔍 Starting comparison of .go and .sql files with project root..."

for dir in "${DIRS[@]}"; do
  echo -e "\n📁 Checking in directory: $dir"

  # Найти все .go и .sql файлы внутри поддиректории
  while IFS= read -r file_in_dir; do
    relative_path="${file_in_dir#$dir/}"  # относительный путь
    file_in_root="./$relative_path"

    if [ -f "$file_in_root" ]; then
      # сравниваем содержимое
      if diff -q "$file_in_dir" "$file_in_root" >/dev/null; then
        echo "✅ Identical: $file_in_dir == $file_in_root"
      else
        echo "❌ DIFFERENT: $file_in_dir != $file_in_root"
        echo "🔎 Diff:"
        diff "$file_in_dir" "$file_in_root" || true  # продолжаем выполнение даже при отличиях
      fi
    else
      echo "⚠️ Missing in root: $file_in_root (exists in $dir)"
    fi
  done < <(find "$dir" -type f \( -name "*.go" -o -name "*.sql" \))

done

echo -e "\n✅ Comparison finished for all directories."

