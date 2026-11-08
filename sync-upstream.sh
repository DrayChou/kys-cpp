#!/usr/bin/env bash
# 把上游 scarsty/kys-cpp 的新提交合回本地（并推到自己的 fork）
set -e
cd "$(dirname "$0")"

git fetch upstream
if git log --oneline HEAD..upstream/master | grep -q .; then
  echo "上游有新提交："
  git log --oneline HEAD..upstream/master | head -20
  git merge upstream/master --no-edit
  echo "合并完成"
else
  echo "上游没有新提交"
fi

git push origin master
echo "已推送到 origin(DrayChou/kys-cpp)"
