import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def visualize_scan_final():
    """
    最终版可视化：完全模拟 Isaac Lab 输出逻辑
    数值 = 地形高度 - 机器人基座高度
    """
    # 1. 模拟设置
    x_distance = np.linspace(-1.0, 2.0, 300) 
    step_h = 0.2
    
    # 地形高度 (World Z)
    terrain_z = np.zeros_like(x_distance)
    terrain_z[x_distance < 0.0] = 0.0                  # 地面
    terrain_z[(x_distance >= 0.0) & (x_distance < 0.5)] = step_h * 1 # 台阶1 (0.2)
    terrain_z[(x_distance >= 0.5) & (x_distance < 1.0)] = step_h * 2 # 台阶2 (0.4)
    terrain_z[(x_distance >= 1.0) & (x_distance < 1.5)] = step_h * 3 # 台阶3 (0.6)
    terrain_z[x_distance >= 1.5] = step_h * 4          # 台阶4 (0.8)

    # 机器人状态
    # 假设机器人站在台阶2上
    # 台阶2高度 0.4m。机器人身高(腿长)假设 0.5m。
    # 所以基座高度 (Base Z) = 0.4 + 0.5 = 0.9m
    robot_x = 0.75
    base_height = 0.5 # 机器人站立高度
    robot_base_z = (step_h * 2) + base_height # 0.9m
    
    # --- 核心：Isaac Lab 输出值 ---
    # Scan = Terrain_Z - Base_Z
    scan_values = terrain_z - robot_base_z

    # 2. 绘图
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    plt.subplots_adjust(hspace=0.4)

    # --- 图1：物理世界 ---
    ax1.set_title("1. 物理世界 (Base Z = 0.9m)", fontsize=14, fontweight='bold')
    ax1.plot(x_distance, terrain_z, 'k-', linewidth=3, label='地形')
    ax1.fill_between(x_distance, terrain_z, -0.1, color='gray', alpha=0.3)
    
    # 画机器人基座
    rect = patches.Rectangle((robot_x-0.15, robot_base_z-0.1), 0.3, 0.2, color='blue', alpha=0.6, label='机器人基座')
    ax1.add_patch(rect)
    # 画腿 (示意)
    ax1.plot([robot_x, robot_x], [robot_base_z-0.1, step_h*2], 'b--', linewidth=2)
    
    ax1.axhline(robot_base_z, color='blue', linestyle='--', alpha=0.5)
    ax1.text(-0.9, robot_base_z+0.05, "基座高度平面", color='blue')
    ax1.legend()
    ax1.grid(True, linestyle=':')

    # --- 图2：传感器输出数值 ---
    ax2.set_title("2. 传感器输出值 (Tensor数值)\n公式: Terrain_Z - Base_Z", fontsize=14, fontweight='bold', color='red')
    ax2.plot(x_distance, scan_values, 'r-', linewidth=3)
    
    # 关键点标注
    # 1. 脚下 (平地)
    # 地形 0.4 - 基座 0.9 = -0.5
    ax2.scatter([0.75], [-0.5], s=80, c='black')
    ax2.text(0.75, -0.45, "脚下平地\n值: -0.5", ha='center', fontweight='bold')
    
    # 2. 前方台阶
    # 地形 0.6 - 基座 0.9 = -0.3
    ax2.scatter([1.25], [-0.3], s=80, c='black')
    ax2.text(1.25, -0.25, "前方台阶\n值: -0.3\n(数值变大/升高)", ha='center', fontweight='bold')

    ax2.set_ylabel("输出值 (负数)")
    ax2.set_xlabel("距离 (m)")
    ax2.grid(True, linestyle=':')
    
    plt.show()

if __name__ == "__main__":
    visualize_scan_final()