import rclpy
from rclpy.node import Node
import numpy as np
from scipy.spatial import KDTree
import heapq
import time

# ROS 2 消息类型
from sensor_msgs.msg import PointCloud2, PointField
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Header
from visualization_msgs.msg import Marker, MarkerArray

# 用于 numpy 和 PointCloud2 之间转换的辅助库
# 在ROS 2 Humble中，这个库通常是预装的
from sensor_msgs_py import point_cloud2

class PointCloudPathPlannerNode(Node):
    def __init__(self):
        super().__init__('pointcloud_path_planner_node')

        # --- ROS 2 参数声明 ---
        self.declare_parameter('area_size', 50.0)
        self.declare_parameter('voxel_size', 0.5) # 这是您可以手动指定的关键参数！
        self.declare_parameter('connection_radius', 0.8)
        self.declare_parameter('start_pos', [-20.0, -20.0, 0.0])
        self.declare_parameter('end_pos', [20.0, 20.0, 3.0])

        # --- ROS 2 发布器 ---
        self.map_pub = self.create_publisher(PointCloud2, 'map_cloud', 10)
        self.path_pub = self.create_publisher(Path, 'planned_path', 10)
        self.marker_pub = self.create_publisher(MarkerArray, 'start_end_markers', 10)
        
        self.get_logger().info("路径规划节点已启动。正在生成场景和规划路径...")
        
        # 执行主逻辑
        self.plan_and_publish()

    def plan_and_publish(self):
        # 获取参数
        area_size = self.get_parameter('area_size').get_parameter_value().double_value
        voxel_size = self.get_parameter('voxel_size').get_parameter_value().double_value
        connection_radius = self.get_parameter('connection_radius').get_parameter_value().double_value
        start_pos = np.array(self.get_parameter('start_pos').get_parameter_value().double_array_value)
        end_pos = np.array(self.get_parameter('end_pos').get_parameter_value().double_array_value)

        # 1. 生成大规模密集点云
        t0 = time.time()
        raw_points = self.create_large_scene(area_size)
        t1 = time.time()
        self.get_logger().info(f"生成 {len(raw_points)} 个原始点云耗时: {t1-t0:.2f} 秒")

        # 2. 体素下采样
        downsampled_points = self.voxel_downsample(raw_points, voxel_size)
        t2 = time.time()
        self.get_logger().info(f"体素滤波 (voxel_size={voxel_size}m) 后剩余 {len(downsampled_points)} 个点。耗时: {t2-t1:.2f} 秒")

        # 3. 构建图
        graph = self.build_graph(downsampled_points, connection_radius)
        t3 = time.time()
        self.get_logger().info(f"构建邻接图耗时: {t3-t2:.2f} 秒")

        # 4. A* 寻路
        kdtree = KDTree(downsampled_points)
        _, start_idx = kdtree.query(start_pos)
        _, end_idx = kdtree.query(end_pos)
        path_indices = self.a_star_search(downsampled_points, graph, start_idx, end_idx)
        t4 = time.time()
        self.get_logger().info(f"A* 寻路耗时: {t4-t3:.2f} 秒")

        # 5. 准备ROS消息
        header = Header(stamp=self.get_clock().now().to_msg(), frame_id='map')
        map_msg = self.create_pointcloud2_msg(downsampled_points, header)
        path_msg = self.create_path_msg(downsampled_points, path_indices, header)
        marker_msg = self.create_marker_msg(downsampled_points[start_idx], downsampled_points[end_idx], header)
        
        # 6. 创建一个定时器来周期性发布，确保RViz可以接收到
        self.timer = self.create_timer(1.0, lambda: self.publish_topics(map_msg, path_msg, marker_msg))
        self.get_logger().info("计算完成！正在通过ROS 2话题发布地图和路径...")

    def publish_topics(self, map_msg, path_msg, marker_msg):
        self.map_pub.publish(map_msg)
        self.path_pub.publish(path_msg)
        self.marker_pub.publish(marker_msg)

    def create_large_scene(self, size=50.0):
        # 基于之前的逻辑，扩大规模
        n_floor = int(2000 * (size/10)**2)
        n_stairs_per_leg = int(1000 * (size/10))
        n_landing = int(200 * (size/10))
        floor_height = 3.0
        
        points = []
        # 一楼和二楼
        floor_xy = np.random.rand(n_floor, 2) * size - (size/2)
        points.append(np.hstack([floor_xy, np.zeros((n_floor, 1))]))
        points.append(np.hstack([floor_xy, np.full((n_floor, 1), floor_height)]))
        
        # U型楼梯
        stair_start_x = size / 2 - 2.0
        stair_width = 2.0
        landing_depth = 4.0
        
        z1 = np.linspace(0, floor_height / 2, n_stairs_per_leg)
        x1 = np.full_like(z1, stair_start_x) + np.random.uniform(-stair_width/2, stair_width/2, z1.shape)
        y1 = np.linspace(0, landing_depth, n_stairs_per_leg)
        points.append(np.vstack([x1, y1, z1]).T)

        landing_x = np.linspace(stair_start_x, stair_start_x - landing_depth, n_landing)
        landing_y = np.full_like(landing_x, landing_depth) + np.random.uniform(-stair_width/2, stair_width/2, landing_x.shape)
        points.append(np.vstack([landing_x, landing_y, np.full_like(landing_x, floor_height / 2)]).T)

        z2 = np.linspace(floor_height / 2, floor_height, n_stairs_per_leg)
        x2 = np.full_like(z2, stair_start_x - landing_depth) + np.random.uniform(-stair_width/2, stair_width/2, z2.shape)
        y2 = np.linspace(landing_depth, 0, n_stairs_per_leg)
        points.append(np.vstack([x2, y2, z2]).T)

        return np.vstack(points)

    def voxel_downsample(self, points, voxel_size):
        # 创建一个字典来存储每个体素中的点
        voxel_dict = {}
        for point in points:
            # 计算体素的索引
            voxel_index = tuple(np.floor(point / voxel_size).astype(int))
            if voxel_index not in voxel_dict:
                voxel_dict[voxel_index] = []
            voxel_dict[voxel_index].append(point)
        
        # 计算每个体素中所有点的质心
        downsampled_points = []
        for voxel_index in voxel_dict:
            downsampled_points.append(np.mean(voxel_dict[voxel_index], axis=0))
            
        return np.array(downsampled_points)

    def build_graph(self, points, connection_radius):
        graph = {}
        kdtree = KDTree(points)
        neighbors_list = kdtree.query_ball_tree(kdtree, r=connection_radius)
        for i, neighbors in enumerate(neighbors_list):
            graph[i] = [n for n in neighbors if n != i]
        return graph
    
    def a_star_search(self, points, graph, start_node_idx, end_node_idx):
        # A* 算法和之前一样
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
                return path[::-1]
            for neighbor_idx in graph.get(current_idx, []):
                tentative_g_score = g_score[current_idx] + np.linalg.norm(points[current_idx] - points[neighbor_idx])
                if tentative_g_score < g_score[neighbor_idx]:
                    came_from[neighbor_idx] = current_idx
                    g_score[neighbor_idx] = tentative_g_score
                    f_score[neighbor_idx] = tentative_g_score + heuristic(neighbor_idx, end_node_idx)
                    heapq.heappush(open_set, (f_score[neighbor_idx], neighbor_idx))
        return None

    def create_pointcloud2_msg(self, points, header):
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)
        ]
        return point_cloud2.create_cloud(header, fields, points)
    
    def create_path_msg(self, points, path_indices, header):
        path_msg = Path()
        path_msg.header = header
        if path_indices:
            for idx in path_indices:
                pose = PoseStamped()
                pose.header = header
                pose.pose.position.x = points[idx][0]
                pose.pose.position.y = points[idx][1]
                pose.pose.position.z = points[idx][2]
                path_msg.poses.append(pose)
        return path_msg
    
    def create_marker_msg(self, start_point, end_point, header):
        marker_array = MarkerArray()
        # Start marker
        start_marker = Marker()
        start_marker.header = header
        start_marker.ns = "start_end"
        start_marker.id = 0
        start_marker.type = Marker.SPHERE
        start_marker.action = Marker.ADD
        start_marker.pose.position.x = start_point[0]
        start_marker.pose.position.y = start_point[1]
        start_marker.pose.position.z = start_point[2]
        start_marker.scale.x = 2.0 * self.get_parameter('voxel_size').get_parameter_value().double_value
        start_marker.scale.y = 2.0 * self.get_parameter('voxel_size').get_parameter_value().double_value
        start_marker.scale.z = 2.0 * self.get_parameter('voxel_size').get_parameter_value().double_value
        start_marker.color.a = 1.0
        start_marker.color.r = 0.0
        start_marker.color.g = 1.0
        start_marker.color.b = 0.0
        
        # End marker
        end_marker = Marker()
        end_marker.header = header
        end_marker.ns = "start_end"
        end_marker.id = 1
        end_marker.type = Marker.SPHERE
        end_marker.action = Marker.ADD
        end_marker.pose.position.x = end_point[0]
        end_marker.pose.position.y = end_point[1]
        end_marker.pose.position.z = end_point[2]
        end_marker.scale = start_marker.scale
        end_marker.color.a = 1.0
        end_marker.color.r = 1.0
        end_marker.color.g = 0.0
        end_marker.color.b = 0.0

        marker_array.markers.append(start_marker)
        marker_array.markers.append(end_marker)
        return marker_array

def main(args=None):
    rclpy.init(args=args)
    node = PointCloudPathPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()