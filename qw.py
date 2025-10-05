import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
import heapq

# --- 1. 创建可扩展的多层建筑场景 ---
def create_multi_story_scene(num_floors=4, n_points_per_floor=4000, n_points_per_stair_leg=1000, n_landing=200):
    """
    生成一个可指定层数的、保证完全连通的场景点云
    - num_floors: 建筑的总层数
    """
    if num_floors < 2:
        raise ValueError("建筑至少需要2层")

    points = []
    floor_height = 3.0
    floor_size = 10.0
    
    # --- 使用循环创建所有楼板 ---
    print(f"正在创建 {num_floors} 个楼板...")
    for i in range(num_floors):
        current_z = i * floor_height
        floor_xy = np.random.rand(n_points_per_floor, 2) * floor_size - (floor_size / 2) # X, Y in [-5, 5]
        floor_points = np.hstack([floor_xy, np.full((n_points_per_floor, 1), current_z)])
        points.append(floor_points)

    # --- 使用循环创建连接楼板的楼梯 ---
    # N层楼需要 N-1 段楼梯
    print(f"正在创建 {num_floors - 1} 段楼梯...")
    for i in range(num_floors - 1):
        # 计算当前这段楼梯的起始、中间和结束高度
        z_start = i * floor_height
        z_mid = z_start + floor_height / 2
        z_end = (i + 1) * floor_height

        stair_start_x = floor_size / 2  # 将楼梯固定在X轴正方向边缘
        stair_width = 1.0
        landing_depth = 2.0
        
        # 第一段楼梯: 从 z_start 上升到 z_mid
        z1 = np.linspace(z_start, z_mid, n_points_per_stair_leg)
        x1 = np.full_like(z1, stair_start_x) + np.random.uniform(-stair_width/2, stair_width/2, z1.shape)
        y1 = np.linspace(0, landing_depth, n_points_per_stair_leg)
        stair1_points = np.vstack([x1, y1, z1]).T
        points.append(stair1_points)

        # 中间平台: 高度为 z_mid
        landing_x = np.linspace(stair_start_x, stair_start_x - landing_depth, n_landing)
        landing_y = np.full_like(landing_x, landing_depth) + np.random.uniform(-stair_width/2, stair_width/2, landing_x.shape)
        landing_points = np.vstack([landing_x, landing_y, np.full_like(landing_x, z_mid)]).T
        points.append(landing_points)

        # 第二段楼梯: 从 z_mid 上升到 z_end
        z2 = np.linspace(z_mid, z_end, n_points_per_stair_leg)
        x2 = np.full_like(z2, stair_start_x - landing_depth) + np.random.uniform(-stair_width/2, stair_width/2, z2.shape)
        y2 = np.linspace(landing_depth, 0, n_points_per_stair_leg)
        stair2_points = np.vstack([x2, y2, z2]).T
        points.append(stair2_points)

    all_points = np.vstack(points)
    return all_points

# --- 2. 构建连通图 (代码与之前相同) ---
def build_graph(points, connection_radius=0.4):
    print(f"正在从 {len(points)} 个点构建图...")
    graph = {}
    kdtree = KDTree(points)
    neighbors_list = kdtree.query_ball_tree(kdtree, r=connection_radius)
    for i, neighbors in enumerate(neighbors_list):
        connections = [n for n in neighbors if n != i]
        graph[i] = connections
    print("图构建完成！")
    return graph

# --- 3. A* 路径规划算法 (代码与之前相同) ---
def a_star_search(points, graph, start_node_idx, end_node_idx):
    print(f"正在从节点 {start_node_idx} 搜索到节点 {end_node_idx}...")
    def heuristic(a_idx, b_idx):
        return np.linalg.norm(points[a_idx] - points[b_idx])
    open_set = [(0, start_node_idx)]
    came_from = {}
    g_score = {i: float('inf') for i in range(len(points))}
    g_score[start_node_idx] = 0
    f_score = {i: float('inf') for i in range(len(points))}
    f_score[start_node_idx] = heuristic(start_node_idx, end_node_idx)

    while open_set:
        _, current_idx = heapq.heappop(open_set)
        if current_idx == end_node_idx:
            path = []
            while current_idx in came_from:
                path.append(current_idx)
                current_idx = came_from[current_idx]
            path.append(start_node_idx)
            print("成功找到路径！")
            return path[::-1]
        for neighbor_idx in graph.get(current_idx, []):
            tentative_g_score = g_score[current_idx] + np.linalg.norm(points[current_idx] - points[neighbor_idx])
            if tentative_g_score < g_score[neighbor_idx]:
                came_from[neighbor_idx] = current_idx
                g_score[neighbor_idx] = tentative_g_score
                f_score[neighbor_idx] = tentative_g_score + heuristic(neighbor_idx, end_node_idx)
                if (f_score[neighbor_idx], neighbor_idx) not in open_set:
                    heapq.heappush(open_set, (f_score[neighbor_idx], neighbor_idx))
    print("未能找到路径！")
    return None

# --- 4. 可视化 (代码与之前相同) ---
def visualize(points, start_point, end_point, path_indices, num_floors):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], s=1, c='gray', alpha=0.1, label='Traversable Surface')
    ax.scatter(start_point[0], start_point[1], start_point[2], c='green', s=150, label='Start', depthshade=False)
    ax.scatter(end_point[0], end_point[1], end_point[2], c='red', s=150, label='End', depthshade=False)
    if path_indices:
        path_points = points[path_indices]
        ax.plot(path_points[:, 0], path_points[:, 1], path_points[:, 2], c='blue', linewidth=4, label='Path')
        ax.scatter(path_points[:, 0], path_points[:, 1], path_points[:, 2], c='blue', s=25, depthshade=False)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title(f'Pathfinding in a {num_floors}-Story Building')
    ax.legend()
    # 调整视角以更好地展示多层结构
    ax.view_init(elev=20., azim=-75)
    plt.show()

# --- 主程序 ---
if __name__ == '__main__':
    # --- 在这里轻松修改总层数 ---
    TOTAL_FLOORS = 8

    # 1. 生成指定层数的场景点云
    scene_points = create_multi_story_scene(num_floors=TOTAL_FLOORS)

    # 2. 构建邻接图
    graph = build_graph(scene_points, connection_radius=0.4)

    # 3. 定义起点(一楼)和终点(顶楼)
    start_pos = np.array([-4.0, -4.0, 0.0]) # 起点在Z=0
    
    # 终点Z坐标需要根据总层数动态计算
    end_z = (TOTAL_FLOORS - 1) * 3.0
    end_pos = np.array([-4.0, 4.0, end_z])
    
    print(f"寻路目标: 从 {start_pos} 到 {end_pos}")

    kdtree = KDTree(scene_points)
    _, start_idx = kdtree.query(start_pos)
    _, end_idx = kdtree.query(end_pos)

    # 4. 运行A*算法寻路
    path = a_star_search(scene_points, graph, start_idx, end_idx)

    # 5. 可视化结果
    visualize(scene_points, scene_points[start_idx], scene_points[end_idx], path, num_floors=TOTAL_FLOORS)