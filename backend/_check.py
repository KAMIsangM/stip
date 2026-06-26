import sqlite3, json
conn = sqlite3.connect('data/smart_teaching.db')
cur = conn.cursor()

# 课程13的 content_modules（通过 chapters 关联）
cur.execute("""
    SELECT cm.id, cm.chapter_id, cm.modal_type, cm.content_json, cm.file_path
    FROM content_modules cm
    JOIN chapters ch ON cm.chapter_id = ch.id
    WHERE ch.course_id = 13
    ORDER BY ch."order", cm.modal_type
""")
rows = cur.fetchall()
print(f"Course 13: {len(rows)} modules")
for r in rows:
    json_str = r[3]
    if json_str:
        try:
            parsed = json.loads(json_str)
            print(f"  ch={r[1]} type={r[2]} file={r[4]}")
            print(f"    json keys: {list(parsed.keys())}")
            print(f"    json: {json.dumps(parsed, ensure_ascii=False)[:200]}")
        except:
            print(f"  ch={r[1]} type={r[2]} file={r[4]} raw={json_str[:100]}")
    else:
        print(f"  ch={r[1]} type={r[2]} file={r[4]} json=None")

# 课程1的 content_modules
print("\n--- Course 1 modules ---")
cur.execute("""
    SELECT cm.id, cm.chapter_id, cm.modal_type, cm.content_json, cm.file_path
    FROM content_modules cm
    JOIN chapters ch ON cm.chapter_id = ch.id
    WHERE ch.course_id = 1
    ORDER BY ch."order", cm.modal_type
""")
rows = cur.fetchall()
print(f"Course 1: {len(rows)} modules")
for r in rows:
    print(f"  ch={r[1]} type={r[2]} json={r[3]} file={r[4]}")

conn.close()
