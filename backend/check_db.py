import sqlite3
conn = sqlite3.connect('e:/2026hot/final/stip/backend/data/smart_teaching.db')
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cur.fetchall()])

# 查看所有课程
cur.execute("SELECT id, title, status, created_at FROM courses ORDER BY id ASC")
print("\nAll courses:")
for r in cur.fetchall():
    print(f"  id={r[0]}, title={r[1]}, status={r[2]}, created_at={r[3]}")

# 查看 chapters
cur.execute("SELECT id, course_id, title FROM chapters ORDER BY course_id, \"order\"")
print("\nChapters:")
for r in cur.fetchall():
    print(f"  id={r[0]}, course_id={r[1]}, title={r[2]}")

conn.close()
