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
        self.scene.robot = QMINI_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")


