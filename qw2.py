import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
import heapq

# --- 1. 创建带螺旋楼梯的多层建筑场景 ---
def create_multi_story_scene_with_spiral_stairs(num_floors=3, n_points_per_floor=8000, n_points_per_stair=5000):
    """
    生成一个可指定层数的、带中心柱螺旋楼梯的场景点云
    """
    if num_floors < 2:
        raise ValueError("建筑至少需要2层")

    points = []
    floor_height = 3.0
    floor_size = 15.0 # 稍微增大场地以便观察
    
    # --- 螺旋楼梯参数 ---
    stair_center_xy = [0.0, 0.0]
    center_column_radius = 0.3 # 中心实心柱的半径
    stair_outer_radius = 2.0   # 楼梯外缘半径
    
    # --- 使用循环创建所有带圆形空洞的楼板 ---
    print(f"正在创建 {num_floors} 个带圆形空洞的楼板...")
    for i in range(num_floors):
        current_z = i * floor_height
        
        # 先生成一个完整的实心楼板
        floor_xy_raw = np.random.rand(n_points_per_floor, 2) * floor_size - (floor_size / 2)
        
        # 计算每个点到楼梯中心的距离
        dist_from_center = np.sqrt(
            (floor_xy_raw[:, 0] - stair_center_xy[0])**2 + 
            (floor_xy_raw[:, 1] - stair_center_xy[1])**2
        )
        
        # 筛选掉楼梯空洞区域内的点
        floor_xy_filtered = floor_xy_raw[dist_from_center > stair_outer_radius]
        
        floor_points = np.hstack([floor_xy_filtered, np.full((floor_xy_filtered.shape[0], 1), current_z)])
        points.append(floor_points)

    # --- 使用循环创建连接楼板的螺旋楼梯 ---
    print(f"正在创建 {num_floors - 1} 段螺旋楼梯...")
    for i in range(num_floors - 1):
        z_start = i * floor_height
        z_end = (i + 1) * floor_height

        # 参数化生成螺旋面
        # 半径r在中心柱外到楼梯边缘之间随机
        r = np.random.uniform(center_column_radius, stair_outer_radius, n_points_per_stair)
        
        # 角度theta。每层楼旋转1.5圈 (3*pi)
        start_angle = i * 3 * np.pi
        end_angle = (i + 1) * 3 * np.pi
        theta = np.random.uniform(start_angle, end_angle, n_points_per_stair)
        
        # 高度z与角度theta成正比
        z = z_start + (theta - start_angle) / (end_angle - start_angle) * floor_height
        
        # 从圆柱坐标转换为笛卡尔坐标
        x = stair_center_xy[0] + r * np.cos(theta)
        y = stair_center_xy[1] + r * np.sin(theta)
        
        stair_points = np.vstack([x, y, z]).T
        points.append(stair_points)

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
    # (此函数无需任何修改)
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
            path = [];
            while current_idx in came_from:
                path.append(current_idx);
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
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], s=1, c='gray', alpha=0.1, label='Traversable Surface')
    ax.scatter(start_point[0], start_point[1], start_point[2], c='green', s=200, label='Start', depthshade=False, marker='o')
    ax.scatter(end_point[0], end_point[1], end_point[2], c='red', s=200, label='End', depthshade=False, marker='x')
    if path_indices:
        path_points = points[path_indices]
        ax.plot(path_points[:, 0], path_points[:, 1], path_points[:, 2], c='blue', linewidth=4, label='Path')
        ax.scatter(path_points[:, 0], path_points[:, 1], path_points[:, 2], c='blue', s=25, depthshade=False)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title(f'Pathfinding in a {num_floors}-Story Building with Spiral Staircase')
    ax.legend()
    # 调整视角以更好地展示螺旋楼梯
    ax.view_init(elev=40., azim=-65)
    ax.set_box_aspect((1, 1, 1)) # 让XYZ轴比例尺相同
    plt.show()

# --- 主程序 ---
if __name__ == '__main__':
    # --- 在这里轻松修改总层数 ---
    TOTAL_FLOORS = 3

    # 1. 生成带螺旋楼梯的场景点云
    scene_points = create_multi_story_scene_with_spiral_stairs(num_floors=TOTAL_FLOORS)

    # 2. 构建邻接图
    graph = build_graph(scene_points, connection_radius=0.5) # 半径可适当调整

    # 3. 定义起点(一楼)和终点(顶楼)
    start_pos = np.array([6.0, 0.0, 0.0]) # 起点在Z=0
    
    # 终点Z坐标需要根据总层数动态计算
    end_z = (TOTAL_FLOORS - 1) * 3.0
    end_pos = np.array([-6.0, 0.0, 3])
    
    print(f"寻路目标: 从 {start_pos} 到 {end_pos}")

    kdtree = KDTree(scene_points)
    _, start_idx = kdtree.query(start_pos)
    _, end_idx = kdtree.query(end_pos)

    # 4. 运行A*算法寻路
    path = a_star_search(scene_points, graph, start_idx, end_idx)

    # 5. 可视化结果
    visualize(scene_points, scene_points[start_idx], scene_points[end_idx], path, num_floors=TOTAL_FLOORS)