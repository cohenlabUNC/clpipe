import clpipe.clpipe

def GLMSetupApp(clpipe.BIDSApp):
    def __init__(subjects = None, config_file=None, glm_config_file = None,
        submit=False, distribute=False, debug = None, drop_tps = None):

        super(name="GLM-Setup", config_file=config_file, distribute=distribute, debug=debug)

        subjects = subjects
        glm_config_file = glm_config_file
        drop_tps = drop_tps