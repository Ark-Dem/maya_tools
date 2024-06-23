from ark_menu_tools import *


ark_menu_create(
	['Relicts', 'ark_menu',

	'Project Manager',								'from ark_projectManager import *; ark_projectManager()', 
	'Kick Maya ASS',								'from ark_mtoa import *; ark_mtoa()',
#	'Geometry Cache',								'from ark_geoCacheAbc import *; ark_geoCacheAbc()',
	'Playblast',									'from ark_playblast import *; ark_playblast()',
	'----',
	['Modeling',
		['Create Grounded Primitive...',
			'Cube',									'from ark_utils import *; ark_utils_groundPrims( "cube" )',
			'Sphere',								'from ark_utils import *; ark_utils_groundPrims( "sphere" )',
			'Cylinder',								'from ark_utils import *; ark_utils_groundPrims( "cyl" )'
		],
		['Set Pivot...',
			'Origin',								'from ark_utils import *; ark_utils_placePivot( "origin" )',
			'Lowest Center',						'from ark_utils import *; ark_utils_placePivot( "base" )',
			'Highest Center',						'from ark_utils import *; ark_utils_placePivot( "top" )',
			'Y=0',									'from ark_utils import *; ark_utils_placePivot( "y0" )',
			'Selected Vertices Center',				'from ark_utils import *; ark_utils_placePivot( "vtxCenter" )'
		],
		'Export Meshes to OBJs (Default Name)',		'from ark_utils import *; ark_utils_objExport()',
		'Export Meshes to OBJs (Custom Name)',		'from ark_utils import *; ark_utils_objExport( named=True )'
	],
	['Animation',
		'Mocap UI',									'import relicts.mocapUI as mocap; mocap.createMocapUI()',
		'Select UI',								'import relicts.selectUI as selUI; selUI.createSelectUI()',
		'Face Tools',								'import faceTools.faceShapeManager as FM; FM.initialize()',
		'Studio Library',							'import studiolibrary; studiolibrary.main()',
		['Poses...',
			'Girl - Default -X',					'from ark_charPose import *; ark_charPose_girl( -90 )',
			'Girl - Default +X',					'from ark_charPose import *; ark_charPose_girl( 90 )',
			'Girl - Default -Z',					'from ark_charPose import *; ark_charPose_girl( 180 )'
		]
	],
	['Rigging',
		['Reconnect From-To...',
			'Inputs & Outputs',						'from ark_utils import *; ark_utils_transferConnections( "both" )',
			'Inputs Only',							'from ark_utils import *; ark_utils_transferConnections( "in" )',
			'Output Only',							'from ark_utils import *; ark_utils_transferConnections( "out" )'
		],
		'Disconnect All',							'from ark_utils import *; ark_utils_disconnectAll()',
		'Keep Unconnected in Selection',			'from ark_utils import *; ark_utils_unconnected()',
		'----',
		'Branch Combine',							'from ark_utils import *; ark_utils_branchCombine()',
		'Follicle on Selected',						'from ark_utils import *; ark_utils_follicle()',
		'Hide Selected from GUI',					'from ark_utils import *; ark_utils_ihi0()'
	],
	['FX',
		'Instancer to Geometry',					'from ark_instToGeo import *; ark_instToGeo()',
		'spPaint3d',								'import maya.mel; maya.mel.eval( "spPaint3d" )',
		'Curve Color Tool',							'from ark_crvColor import *; ark_crvColor()',
		'----',
		'Frame Time HUD',							'from ark_playblast import *; headsUpDisplay( "HUDPlayblastRendertime", section = 8, block = 0, dataFontSize = "small", command = "ark_playblast_HUDrtime()", attachToRefresh = True )',
		'Select all nCloth',						'from ark_utils import *; ark_utils_selByType( "nCloth" )',
		'Cache Selected Dynamics',					'from ark_utils import *; ark_utils_cacheDyn()',
		'----',
		'Bifrost Geo to Maya',						'from ark_utils import *; ark_utils_biGeo()'
	],
	['Rendering',
		'Select Geometry in Hierarchy',				'from ark_utils import *; ark_utils_hiGeo()',
		'Select shadingGroups on Selected',			'from ark_utils import *; ark_utils_selSG()',
		'Override Shaders on Selected SGs',			'from ark_utils import *; ark_utils_shdToSG()',
		'----',
		['Create Shading Network',
			'Surface',								'from ark_utils import *; ark_utils_networkTemplate( "arnold5_surface" )'
		],
		'----',
		'Check ColorSpaces Sharing',				'from ark_utils import *; ark_utils_imgCSpaceCheck()',
		'Localize Texture Paths',					'from ark_utils import *; ark_utils_localizeFileNodes( "textures" )',
		'Texture Paths to .tx',						'from ark_utils import *; ark_utils_texPathToTx()',
		'----',
		'Override AOVs to OFF',						'from ark_utils import *; ark_utils_rlayAiAovOff()'
	],
	['Maintenance',
		'Namespace Remover',						'from ark_utils import *; ark_utils_nmRemove()',
		'Add Suffix to Selected Nodes',				'from ark_utils import *; ark_utils_addSuffix()',
		'Fix Shape Names',                          'from ark_utils import *; ark_utils_fixShapeName()',
		'Name File Nodes by Textures',				'from ark_utils import *; ark_utils_nameFileNodes()',
		'Find Same Names',							'from ark_utils import *; ark_utils_findSameNames()',
		'Find Non-Unicode Paths or Names',			'from ark_utils import *; ark_utils_findNonUnicode()',
		'List Attributes and Values',				'from ark_utils import *; ark_utils_attrValues()',
		'----',
		'Save All Attributes Values',				'from ark_utils import *; ark_utils_attrList( read=False )',
		'Restore All Attributes Values',			'from ark_utils import *; ark_utils_attrList( read=True )',
		'----',
		'Delete Unknown Nodes',                     'from ark_utils import *; ark_utils_deleteUnknownNodes()',
		'Remove Unknown Plugins',					'from ark_utils import *; ark_utils_removeUnknownPlugins()',
		'----',
		'Build New Scene UI',						'import maya.mel; maya.mel.eval( "buildNewSceneUI" )',
		'Default Startup Cameras',					'from ark_utils import *; ark_utils_startupCamerasFix()',
		'Change Node\'s Category',					'from ark_utils import *; ark_utils_list()'
	]
	]
)
