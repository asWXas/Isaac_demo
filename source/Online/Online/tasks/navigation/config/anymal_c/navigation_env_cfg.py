# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import math

# --- Isaac Lab Core Imports ---
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import CurriculumTermCfg as CurrTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg, RayCasterCfg, patterns
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR, ISAACLAB_NUCLEUS_DIR
from isaaclab.utils.noise import AdditiveUniformNoiseCfg as Unoise

# --- Pre-defined Configs & Terrains ---
from isaaclab.terrains.config.rough import ROUGH_TERRAINS_CFG
from isaaclab_tasks.manager_based.locomotion.velocity.config.anymal_c.flat_env_cfg import AnymalCFlatEnvCfg
from isaaclab_assets.robots.anymal import ANYMAL_C_CFG  # isort: skip

# --- Logic Imports ---
import Online.tasks.navigation.mdp as mdp          # 你的 MDP 库


# --- Configuration Instances ---
LOW_LEVEL_ENV_CFG = AnymalCFlatEnvCfg()

@configclass
class MySceneCfg(InteractiveSceneCfg):
    """Configuration for the terrain scene with a legged robot."""

    # ground terrain
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="generator",
        terrain_generator=ROUGH_TERRAINS_CFG,
        max_init_terrain_level=5,
        collision_group=-1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
        visual_material=sim_utils.MdlFileCfg(
            mdl_path=f"{ISAACLAB_NUCLEUS_DIR}/Materials/TilesMarbleSpiderWhiteBrickBondHoned/TilesMarbleSpiderWhiteBrickBondHoned.mdl",
            project_uvw=True,
            texture_scale=(0.25, 0.25),
        ),
        debug_vis=False,
    )

    # robots
    robot: ArticulationCfg = ANYMAL_C_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    # sensors
    height_scanner = RayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
        ray_alignment="yaw",
        pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=[1.6, 1.0]),
        debug_vis=False,
        mesh_prim_paths=["/World/ground"],
    )
    
    height_scanner_2 = RayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base",
        offset=RayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 20.0)),
        ray_alignment="yaw",
        pattern_cfg=patterns.GridPatternCfg(resolution=0.1, size=[1.6, 1.0]),
        debug_vis=False,
        mesh_prim_paths=["/World/ground"],
    )
    
    
    
    
    contact_forces = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/.*", 
        history_length=3, 
        track_air_time=True
    )

    # lights
    sky_light = AssetBaseCfg(
        prim_path="/World/skyLight",
        spawn=sim_utils.DomeLightCfg(
            intensity=750.0,
            texture_file=f"{ISAAC_NUCLEUS_DIR}/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr",
        ),
    )

@configclass
class EventCfg:
    """事件配置 (Reset)"""
    reset_base = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14)},
            "velocity_range": {
                "x": (-0.0, 0.0), "y": (-0.0, 0.0), "z": (-0.0, 0.0),
                "roll": (-0.0, 0.0), "pitch": (-0.0, 0.0), "yaw": (-0.0, 0.0),
            },
        },
    )


@configclass
class ActionsCfg:
    """动作配置"""
    pre_trained_policy_action: mdp.PreTrainedPolicyActionCfg = mdp.PreTrainedPolicyActionCfg(
        asset_name="robot",
        policy_path=f"{ISAACLAB_NUCLEUS_DIR}/Policies/ANYmal-C/Blind/policy.pt",
        low_level_decimation=4,
        low_level_actions=LOW_LEVEL_ENV_CFG.actions.joint_pos,
        low_level_observations=LOW_LEVEL_ENV_CFG.observations.policy,
    )


@configclass
class ObservationsCfg:
    """观测配置 (Policy Inputs)"""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy group."""

        # 1. 自身状态: 速度
        base_lin_vel = ObsTerm(func=mdp.base_lin_vel)
        
        # 2. 环境感知: 高度扫描 (从 height_scanner_2 获取)
        height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("height_scanner_2")},
            noise=Unoise(n_min=-0.1, n_max=0.1),
            clip=(-1.0, 1.0),
        )
        
        # 3. 自身状态: 重力方向 (感知姿态/坡度)
        projected_gravity = ObsTerm(func=mdp.projected_gravity)
        
        # 4. 任务目标: XYW 指令
        pose_command = ObsTerm(
            func=mdp.generated_commands, 
            params={"command_name": "pose_command"}
        )

    policy: PolicyCfg = PolicyCfg()


@configclass
class RewardsCfg:
    """奖励函数配置 (The Objective)"""

    # --- 1. 任务主线 (Task) ---
    
    # [高额奖励] 到达目标 (Success Bonus)
    success = RewTerm(
        func=mdp.success_bonus,
        weight=200.0,
        params={"threshold": 0.5, "command_name": "pose_command"},
    )

    # [隐式计时] 生存惩罚 (Alive Penalty)
    # 迫使智能体尽快完成任务以停止扣分
    alive_penalty = RewTerm(func=mdp.is_alive, weight=-0.05)
    
    # [驱动力] 进度奖励 (Progress)
    # 奖励向目标方向的速度投影
    progress = RewTerm(
        func=mdp.progress_toward_target,
        weight=0.5,
        params={"command_name": "pose_command"},
    )
    
    # [辅助] 位置追踪 (Position Tracking)
    position_tracking = RewTerm(
        func=mdp.position_command_error_tanh,
        weight=1.0,
        params={"std": 2.0, "command_name": "pose_command"},
    )

    # [辅助] 朝向追踪 (Heading Tracking)
    orientation_tracking = RewTerm(
        func=mdp.heading_command_error_abs,
        weight=-0.5,
        params={"command_name": "pose_command"},
    )

    # --- 2. 稳定性与 3D 适应 (Stability) ---

    # [楼梯适应] 垂直稳定惩罚
    # 抑制 Z 轴剧烈运动，防止在楼梯上跳跃或跌落
    stable_motion = RewTerm(
        func=mdp.penalize_vertical_motion,
        weight=-1.0,
    )

    # --- 3. 安全性 (Safety) ---

    # [避障] 碰撞惩罚
    # 任何非脚部碰撞都会导致严重扣分
    collision = RewTerm(
        func=mdp.undemanded_collision,
        weight=-5.0,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces"), 
            "threshold": 10.0
        },
    )
    
    # [失败] 终止惩罚
    termination_penalty = RewTerm(func=mdp.is_terminated, weight=-200.0)

    # --- 4. 平滑性 (Smoothness) ---

    # [L2 正则] 动作平滑
    # 使用平方差，抑制抖动，允许微调
    action_rate = RewTerm(
        func=mdp.action_rate_penalty,
        weight=-0.1,
    )


@configclass
class CommandsCfg:
    """指令生成配置"""
    pose_command = mdp.UniformPose2dCommandCfg(
        asset_name="robot",
        simple_heading=False,
        resampling_time_range=(8.0, 8.0),
        debug_vis=True,
        ranges=mdp.UniformPose2dCommandCfg.Ranges(
            pos_x=(-3.0, 3.0), 
            pos_y=(-3.0, 3.0), 
            heading=(-math.pi, math.pi)
        ),
    )


@configclass
class TerminationsCfg:
    """终止条件配置"""

    # 1. 时间耗尽
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    
    # 2. 严重碰撞 (基座撞击)
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={
            "sensor_cfg": SceneEntityCfg("contact_forces", body_names="base"), 
            "threshold": 1.0
        },
    )
    
    # 3. 任务完成 (到达目标)
    # 触发重置，开始下一轮训练
    reached_target = DoneTerm(
        func=mdp.has_reached_target,
        params={"threshold": 0.5, "command_name": "pose_command"},
    )


@configclass
class NavigationEnvCfg(ManagerBasedRLEnvCfg):
    """环境总配置"""
    scene: SceneEntityCfg = MySceneCfg()
    actions: ActionsCfg = ActionsCfg()
    observations: ObservationsCfg = ObservationsCfg()
    events: EventCfg = EventCfg()
    commands: CommandsCfg = CommandsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self) -> None:
        """Post initialization."""
        self.sim.dt = LOW_LEVEL_ENV_CFG.sim.dt
        self.sim.render_interval = LOW_LEVEL_ENV_CFG.decimation
        self.decimation = LOW_LEVEL_ENV_CFG.decimation * 10
        self.episode_length_s = self.commands.pose_command.resampling_time_range[1]

        # 更新传感器频率
        if self.scene.height_scanner_2 is not None:
            self.scene.height_scanner_2.update_period = (
                self.actions.pre_trained_policy_action.low_level_decimation * self.sim.dt
            )
            
        if self.scene.height_scanner is not None:
            self.scene.height_scanner.update_period = (
            self.actions.pre_trained_policy_action.low_level_decimation * self.sim.dt
            )
        if self.scene.contact_forces is not None:
            self.scene.contact_forces.update_period = self.sim.dt