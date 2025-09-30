场景设置 (_setup_scene): 初始化机器人、传感器和地形。

动作处理 (_pre_physics_step, _apply_action): 接收来自强化学习代理的动作并将其应用于机器人。

观测生成 (_get_observations): 从仿真中收集状态信息，作为 RL 代理的输入。

奖励计算 (_get_rewards): 根据机器人的表现计算奖励信号。

终止判断 (_get_dones): 判断当前回合（episode）是否应该结束。

环境重置 (_reset_idx): 在回合结束后重置环境和机器人状态。