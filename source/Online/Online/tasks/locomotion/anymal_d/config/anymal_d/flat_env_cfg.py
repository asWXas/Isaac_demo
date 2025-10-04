from isaaclab.utils import configclass

from .rough_env_cfg import AnymalDRoughEnvCfg


# @configclass
# class AnymalDFlatEnvCfg(AnymalDRoughEnvCfg):
#     def __post_init__(self):
#         # post init of parent
#         super().__post_init__()

#         # override rewards
#         self.rewards.flat_orientation_l2.weight = -5.0
#         self.rewards.dof_torques_l2.weight = -2.5e-5
#         self.rewards.feet_air_time.weight = 0.5
#         # change terrain to flat
#         self.scene.terrain.terrain_type = "usd"
#         self.scene.terrain.terrain_generator = None
#         # no height scan
#         self.scene.height_scanner = None
#         self.observations.policy.height_scan = None
#         # no terrain curriculum
#         self.curriculum.terrain_levels = None
        
        
# from omni.isaac.lab.utils import configclass
# # 假设 AnymalDRoughEnvCfg 已经从其他地方正确导入
# from .anymal_d_rough_env_cfg import AnymalDRoughEnvCfg


@configclass
class AnymalDFlatEnvCfg(AnymalDRoughEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()

        # ==================================
        # 1. 核心修改：切换到USD地形
        # ==================================
        
        # 将地形类型设置为 "usd"
        self.scene.terrain.terrain_type = "usd"
        # 【关键】添加要加载的USD文件的路径
        # !!! 请将下面的路径替换成你自己的文件路径 !!!
        self.scene.terrain.usd_path = "/home/wx/WS/IsaacLabExtensionTemplate/source/Online/Online/tasks/locomotion/anymal_d/mdp/Xform_01.usd"
        # 移除程序化地形生成器，因为不再需要
        self.scene.terrain.terrain_generator = None

        # ==================================
        # 2. 关联修改：移除不必要的功能
        # ==================================

        # 对于固定的USD地形，通常不需要高度扫描仪
        self.scene.height_scanner = None
        # 同样，从观察中移除高度扫描数据
        self.observations.policy.height_scan = None
        # 对于固定的USD地形，地形难度课程学习无效，将其禁用
        self.curriculum.terrain_levels = None
        
        # ==================================
        # 3. （可选）调整奖励函数以适应平地
        # ==================================
        
        self.rewards.flat_orientation_l2.weight = -5.0
        self.rewards.dof_torques_l2.weight = -2.5e-5
        self.rewards.feet_air_time.weight = 0.5


class AnymalDFlatEnvCfg_PLAY(AnymalDFlatEnvCfg):
    def __post_init__(self) -> None:
        # post init of parent
        super().__post_init__()

        # make a smaller scene for play
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        # disable randomization for play
        self.observations.policy.enable_corruption = False
        # remove random pushing
        self.events.base_external_force_torque = None
        self.events.push_robot = None
