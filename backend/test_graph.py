import requests

# 验证图谱数据
r = requests.get("http://localhost:8000/api/v1/courses/1/knowledge-graph")
data = r.json()
print(f"nodes: {len(data['nodes'])}, edges: {len(data['edges'])}")
print("First 3 nodes:", data["nodes"][:3])
print("First 3 edges:", data["edges"][:3])

# 验证拓扑排序
r2 = requests.get("http://localhost:8000/api/v1/courses/1/knowledge-graph/sorted")
data2 = r2.json()
print(f"sorted nodes: {len(data2['nodes'])}")
print("Sorted order (first 5):", [n["name"] for n in data2["nodes"][:5]])

# 验证预设列表
r3 = requests.get("http://localhost:8000/api/v1/knowledge-graph/presets")
print("presets:", r3.json())
