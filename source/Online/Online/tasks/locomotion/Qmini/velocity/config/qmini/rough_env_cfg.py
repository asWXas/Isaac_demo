from isaaclab.utils import configclass

from Online.tasks.locomotion.velocity.velocity_env_cfg import LocomotionVelocityRoughEnvCfg

##
# Pre-defined configs
##
from Online.Robot.Qmini import QMINI_CFG


@configclass
class QminiRoughEnvCfg(LocomotionVelocityRoughEnvCfg):
    def __post_init__(self):
        super().__post_init__()


    ##########################################   sence ##########################################
        self.scene.robot = QMINI_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        if self.scene.height_scanner:
            self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base_link"
            
    #########################################  events  #############################################
        self.events.push_robot = None
        self.events.add_base_mass = None
        self.events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
        self.events.base_external_force_torque.params["asset_cfg"].body_names = [".*torso_link"]
        self.events.reset_base.params = {
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14),"z":(0.45,0.5)},
            "velocity_range": {
                "x": (0.0, 0.0),
                "y": (0.0, 0.0),
                "z": (0.0, 0.0),
                "roll": (0.0, 0.0),
                "pitch": (0.0, 0.0),
                "yaw": (0.0, 0.0),
            },
        }
        self.events.base_com = None
        
    
    ########################################  observations ##########################################
        self.observations.policy = None
        self.observations.critic = None
    
    #######################################  actions #############################################
    
    #######################################  commands ############################################
    
    
    
    ########################################  rewards  ############################################
    
    
    ######################################  terminations ##########################################
    
    

    
    
    ######################################  curriculum ##########################################