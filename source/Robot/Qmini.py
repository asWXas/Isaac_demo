

import isaaclab.sim as sim_utils
from isaaclab.actuators import ActuatorNetLSTMCfg, DCMotorCfg
from isaaclab.assets.articulation import ArticulationCfg
from isaaclab.sensors import RayCasterCfg

# LL 组（左下肢或类似结构）：

# LL_joint1
# LL_joint2
# LL_joint3
# LL_joint4
# LL_joint5
# RL 组（右下肢或类似结构）：

# RL_joint1
# RL_joint2
# RL_joint3
# RL_joint4
# RL_joint5


QMINI_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=f"/home/wx/WS/IsaacLabExtensionTemplate/source/Online/Asset/Robot/Qmini/Qmini.usd",
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False, solver_position_iteration_count=4, solver_velocity_iteration_count=0
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.45),
        joint_pos={
            ".*L_joint1": 0.0,
            ".*L_joint2": 0.0,
            ".*L_joint3": 0.0,
            ".*L_joint4": 0.0,
            ".*L_joint5": 0.0,
        },
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=0.9,
    actuators={
        "joint1": DCMotorCfg(
            joint_names_expr=[ "LL_joint1", "RL_joint1" ],
            effort_limit=20.0,
            saturation_effort=20.0,
            velocity_limit=57.29578,
            stiffness=47.7,
            damping=0.019057167693972588,
            friction=0.0,
        ),
        "joint2": DCMotorCfg(
            joint_names_expr=[ "LL_joint2", "RL_joint2" ],
            effort_limit=60.0,
            saturation_effort=60.0,
            velocity_limit=17.18873405456543,
            stiffness=63.275856018066406,
            damping=0.025310343131422997,
            friction=0.0,
        ),
        "joint3": DCMotorCfg(
            joint_names_expr=[ "LL_joint3", "RL_joint3" ],
            effort_limit=20.0,
            saturation_effort=20.0,
            velocity_limit=57.2957763671875,
            stiffness=40.45454406738281,
            damping=0.016181817278265953,
            friction=0.0,
        ),
        "joint4": DCMotorCfg(
            joint_names_expr=[ "LL_joint4", "RL_joint4" ],
            effort_limit=20.0,
            saturation_effort=20.0,
            velocity_limit=57.2957763671875,
            stiffness=39.21044158935547,
            damping=0.015684176236391068,
            friction=0.0,
        ),
        "joint5": DCMotorCfg(
            joint_names_expr=[ "LL_joint5", "RL_joint5" ],
            effort_limit=20.0,
            saturation_effort=20.0,
            velocity_limit=57.2957763671875,
            stiffness=7.755740642547607,
            damping=0.0031022962648421526,
            friction=0.0,
        ),
    },
)