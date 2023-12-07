import os
import json
from .options import ProjectOptions, DEFAULT_CONFIG_FILE_NAME

DEFAULT_GLM_CONFIG_FILE_NAME = "defaultGLMConfig.json"

# GLM Levels
VALID_L1 = ["1", "L1", "l1", "level1"]
VALID_L2 = ["2", "L2", "l2", "level2"]
L1 = VALID_L1[1]
L2 = VALID_L2[1]


class GLMOptions:
    """Configuration related to the GLM modules

    Config values are found in this object's 'attribute' as a dictionary matching
        the json structure of the default GLM config file.
    """

    def __init__(self, glm_config_file: os.PathLike = None):
        """
        Args:
            glm_config_file (os.PathLike, optional): Path to GLM config file.
            May be relative. Defaults to None.
        """
        # Use the default GLM config file if none provided
        if glm_config_file is None:
            from pkg_resources import resource_stream

            with resource_stream(
                "clpipe", f"data/{DEFAULT_GLM_CONFIG_FILE_NAME}"
            ) as def_config:
                self.config = json.load(def_config)

            self.parent_options = None
        else:
            with open(os.path.abspath(glm_config_file), "r") as glm_config_file:
                self.config = json.load(glm_config_file)

            # Load in the project options via the parent clpipe config
            self.parent_options = ProjectOptions.load(self.config["ParentClpipeConfig"])

    def config_json_dump(
        self,
        outputdir: os.PathLike,
        file_name: os.PathLike = DEFAULT_GLM_CONFIG_FILE_NAME,
    ) -> os.PathLike:
        """Dump the state of this configuration to json.

        Args:
            outputdir (os.PathLike): Output destination. May be relative.
            file_name (os.PathLike, optional): Name of your GLM config file. Defaults to
            default glm config file name.
        """
        outpath = os.path.join(os.path.abspath(outputdir), file_name)

        with open(outpath, "w") as fp:
            json.dump(self.config, fp, indent="\t")

        return outpath

    def populate_project_paths(self, parent_config_file) -> None:
        """Generate default project paths given a specific project root.

        Args:
            parent_config_file (os.PathLike): Path to the (already populated) parent config file.
        """

        self.config["ParentClpipeConfig"] = parent_config_file

        # Load in the project options via the parent clpipe config to get project
        #   root directory.
        self.parent_options = ProjectOptions.load(parent_config_file)
        project_directory = self.parent_options.project_directory

        self.config["Level1Setups"][0]["TargetDirectory"] = os.path.join(
            project_directory, "data_postproc", "default"
        )
        self.config["Level1Setups"][0]["FSFDir"] = os.path.join(
            project_directory, "l1_fsfs"
        )
        self.config["Level1Setups"][0]["EVDirectory"] = os.path.join(
            project_directory, "data_onsets"
        )
        self.config["Level1Setups"][0]["ConfoundDirectory"] = os.path.join(
            project_directory, "data_postproc", "default"
        )
        self.config["Level1Setups"][0]["OutputDir"] = os.path.join(
            project_directory, "l1_feat_folders"
        )
        self.config["Level1Setups"][0]["LogDir"] = os.path.join(
            project_directory, "logs", "glm_logs", "L1_launch"
        )

        self.config["Level2Setups"][0]["OutputDir"] = os.path.join(
            project_directory, "l2_gfeat_folders"
        )
        self.config["Level2Setups"][0]["FSFDir"] = os.path.join(
            project_directory, "l2_fsfs"
        )
        self.config["Level2Setups"][0]["LogDir"] = os.path.join(
            project_directory, "logs", "glm_logs", "L2_launch"
        )
