# filename: shortest_path.py
import heapq

def dijkstra(graph, start, end):
    # 初始化距离字典，所有点到起点的距离设为无穷大
    distances = {vertex: float('infinity') for vertex in graph}
    # 起点到自身的距离为0
    distances[start] = 0
    # 优先队列，存储(距离, 当前顶点)
    priority_queue = [(0, start)]
    
    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)

        # 如果当前节点是终点，则结束
        if current_vertex == end:
            break
        
        # 遍历当前节点的所有邻居
        for neighbor, weight in graph[current_vertex].items():
            distance = current_distance + weight
            
            # 只有当新路径更短时才更新
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(priority_queue, (distance, neighbor))
                
    return distances[end], reconstruct_path(distances, graph, start, end)

def reconstruct_path(distances, graph, start, end):
    path = [end]
    while end != start:
        for neighbor, weight in graph[end].items():
            if distances[end] == distances[neighbor] + weight:
                path.append(neighbor)
                end = neighbor
                break
    path.reverse()
    return path

# 定义图
graph = {
    'A': {'B': 4, 'C': 2},
    'B': {'C': 1, 'D': 5},
    'C': {'D': 8, 'E': 10},
    'D': {'E': 2, 'F': 6},
    'E': {'F': 2, 'H': 3},
    'F': {'G': 1, 'H': 4},
    'G': {'H': 2},
    'H': {}
}

# 计算并打印最短路径
shortest_distance, path = dijkstra(graph, 'A', 'H')
print(f"最短路径是从 A 到 H: {' -> '.join(path)}")
print(f"总距离: {shortest_distance}")