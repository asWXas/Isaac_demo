# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.sensors import ContactSensor
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


# --- 任务导向 (Task Rewards) ---

def position_command_error_tanh(env: ManagerBasedRLEnv, std: float, command_name: str) -> torch.Tensor:
    """
    基于 Tanh 核的位置追踪奖励。
    用于在靠近目标时提供密集的引导信号。
    """
    command = env.command_manager.get_command(command_name)
    des_pos_b = command[:, :3]
    distance = torch.norm(des_pos_b, dim=1)
    return 1 - torch.tanh(distance / std)


def heading_command_error_abs(env: ManagerBasedRLEnv, command_name: str) -> torch.Tensor:
    """
    朝向误差惩罚 (绝对值)。
    """
    command = env.command_manager.get_command(command_name)
    heading_b = command[:, 3]
    return heading_b.abs()


def progress_toward_target(env: ManagerBasedRLEnv, command_name: str) -> torch.Tensor:
    """
    进度奖励：奖励向目标移动的速度投影。
    这能有效驱动机器人"动起来"，而不仅仅是"位置离得近"。
    Calculation: velocity_vector dot_product (target_direction)
    """
    # 获取目标在基座坐标系下的位置 (xy)
    command = env.command_manager.get_command(command_name)
    target_pos_b = command[:, :2]
    
    # 计算归一化的目标方向向量
    dist = torch.norm(target_pos_b, dim=1, keepdim=True)
    target_dir = target_pos_b / (dist + 1e-5)
    
    # 获取当前基座线速度 (基座坐标系 xy)
    lin_vel_b = env.scene["robot"].data.root_lin_vel_b[:, :2]
    
    # 计算点积：速度在目标方向上的投影
    progress = torch.sum(target_dir * lin_vel_b, dim=1)
    
    return progress


def success_bonus(env: ManagerBasedRLEnv, threshold: float, command_name: str) -> torch.Tensor:
    """
    稀疏成功奖励。
    当距离小于阈值时给予一次性大奖励。
    """
    command = env.command_manager.get_command(command_name)
    des_pos_b = command[:, :3]
    distance = torch.norm(des_pos_b, dim=1)
    
    return (distance < threshold).float()


# --- 安全与稳定性 (Safety & Stability) ---

def undemanded_collision(env: ManagerBasedRLEnv, sensor_cfg: SceneEntityCfg, threshold: float) -> torch.Tensor:
    """
    碰撞惩罚。
    检测非脚部 (Base, Thighs) 的接触力。如果超过阈值，视为碰撞。
    这对避障训练至关重要。
    """
    contact_sensor: ContactSensor = env.scene.sensors[sensor_cfg.name]
    
    # 取最近一帧的力: (num_envs, num_bodies, 3)
    current_forces = contact_sensor.data.net_forces_w_history[:, 0, :, :]
    force_magnitudes = torch.norm(current_forces, dim=-1)
    
    # 任何部位受力超过阈值即为 True
    is_collision = torch.any(force_magnitudes > threshold, dim=1)
    
    return is_collision.float()


def penalize_vertical_motion(env: ManagerBasedRLEnv) -> torch.Tensor:
    """
    垂直稳定性惩罚。
    惩罚 Z 轴速度的平方。
    在楼梯场景中，鼓励机器人走得平稳，防止跳跃或跌落。
    """
    root_vel_w = env.scene["robot"].data.root_lin_vel_w
    return torch.square(root_vel_w[:, 2])


# --- 平滑性 (Smoothness) ---

def action_rate_penalty(env: ManagerBasedRLEnv) -> torch.Tensor:
    """
    L2 动作平滑惩罚 (平方差)。
    Cost = sum((action_t - action_{t-1})^2)
    
    为什么用平方 (L2) 而不用比例 (L1)?
    - L2 允许微小的修正 (0.01^2 = 0.0001, 忽略不计)。
    - L2 严厉禁止剧烈抖动 (0.5^2 = 0.25, 惩罚巨大)。
    - L1 会导致"死区"效应，让机器人变得僵硬，不愿做微调。
    """
    curr_action = env.action_manager.action
    prev_action = env.action_manager.prev_action
    
    diff = (curr_action - prev_action).pow(2).sum(dim=1)
    return diff


# --- 终止判定 (Termination Helper) ---

def has_reached_target(env: ManagerBasedRLEnv, threshold: float, command_name: str) -> torch.Tensor:
    """
    判定是否到达目标（用于重置环境）。
    """
    command = env.command_manager.get_command(command_name)
    des_pos_b = command[:, :3]
    distance = torch.norm(des_pos_b, dim=1)
    return distance < threshold