
MOSHELL = "/app/moshell/latest/moshell/moshell"
MOSHELL_G2_ARGS = 'comcli=21,username=expert,password=expert'
MOSHELL2 = "{} -v '{}'".format(MOSHELL, MOSHELL_G2_ARGS)

MOSHELL_PROMPT_CFG = "ROBOT:="
MOSHELL_ROBOT_CFG = 'set_window_title=0,prompt_highlight=0,show_colors=0,prompt_colors=0,prompt={}'.format(
    MOSHELL_PROMPT_CFG)

MOSHELL_ROBOT1 = "{} -v '{}'".format(MOSHELL, MOSHELL_ROBOT_CFG)
MOSHELL_ROBOT2 = "{} -v '{},{}'".format(MOSHELL, MOSHELL_G2_ARGS,
                                        MOSHELL_ROBOT_CFG)

TTY_WIN_SIZE = (50, 380)

SSH_PROMPT = ":[0-9a-zA-Z_\-/~.]+> \Z"
MOSHELL_PROMPT = "{}> \Z".format(MOSHELL_PROMPT_CFG)
