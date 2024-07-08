from maya.cmds import *


# BUILD CUSTOM MENU
evalDeferred( 'import ark_menu' )


# ADD VIEWPORT FRAME TIME HUD
from ark_playblast import *

headsUpDisplay( 'HUDPlayblastRendertime',
				section = 8,
				block = 0,
				dataFontSize = 'small',
				command = 'ark_playblast_HUDrtime()',
				attachToRefresh = True )
