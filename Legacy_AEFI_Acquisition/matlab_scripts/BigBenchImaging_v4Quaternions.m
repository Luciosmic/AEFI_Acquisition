% The purpose of this script is to process raw data acquired on the all
% electric field (EF) measurement test bench and saved with the LabVIEW
% software
% - Volt to Vmeter
% - Spatial interpolation taking into account acquisition time between each dataset
% - EF components projection from sensor frame to bench frame
% - Offsets and phase shift correction
% - Background removal
% - Median filter
clear all; close all; warning off; %#ok<CLALL>

% Software version
v = 4.0;
fprintf("/-------------------------------------------------\\\n")
fprintf("|           Big Bench Data Analysis v%3.1f          |\n",v)
fprintf("\\-------------------------------------------------/\n")

%% Get the Matlab Script path
if isdeployed % Stand-alone mode.
    [status, result] = system('path');
    mpath = char(regexpi(result, 'Path=(.*?);', 'tokens', 'once'));
else % MATLAB mode.
    mpath = fileparts(mfilename('fullpath'));
    addpath(genpath(mpath))
end

%% Global parameters
global colors; % yellow, pink, red, blue, orange, green, purple, cyan, green2
colors = {[255,255,102], [255,153,255], [255,051,051], [102,178,255], ...
    [255,153,051],[102,255,102],[178,102,255],[102,255,255],[154,205,50]};
%
% %% Definition rotation matrices
Rx = @(x)([1 0 0 ; 0 cosd(x) -sind(x) ; 0 sind(x) cosd(x)]);
Ry = @(x)([cosd(x) 0 sind(x) ; 0 1 0 ; -sind(x) 0 cosd(x)]);
Rz = @(x)([cosd(x) -sind(x) 0 ; sind(x) cosd(x) 0 ; 0 0 1]);

%% Parameters management
% Part1: Default parameters and initialization

% Path to the folder containing data folders
%pathData = 'C:\Users\roblin211\Nextcloud2\Banc de test\Banc de test II\Acquisitions\Data';
% pathData = 'C:\Users\denoual\Unicloud\ASSOCE\Banc de test\Banc de test II\Acquisitions\Data';
pathData = 'C:\Users\saluden231\Nextcloud2\ASSOCE\Banc de test\Banc de test II\Acquisitions\Data';

% Calibration factors
incToMm = 0.0436;                       % spatial conversion from inc to mm
VtoVpm  = 1;                            % signal conversion from V to V/m
offsetE = [0;0;0]; offsetI = [0;0;0];   % offset (no signal)
phaseEI = [0;0;0];                      % phase shift
bgdE    = [0;0;0]; bgdI    = [0;0;0];   % background

% Specify how data are stored in .csv data file (minus sign to reverse axis)
% MAGL sensor
infoM.M = [-4,-3,5];    % Magnetic field [X, Y, Z] --> Stored at rows 3,4,5
infoM.A = [-7,-6,8];    % Accelerometer  [X, Y, Z]
infoM.G = [-10,-9,11];  % Gyrometer      [X, Y, Z]
infoM.L = 12;           % LIDAR          H
infoM.t = 13;           % Time           t
infoM.s = 14;           % Scanning state b
% E sensor
infoE.E = [5,10,15];    % Electric field, real  [X, Y, Z]
infoE.I = [4,9,14];     % Electric field, imag  [X, Y, Z]
infoE.t = [1,6,11];     % Time                  [X, Y, Z] (3 different times because of multiplexing for probe V1)
infoE.s = 16;           % Scanning state        b

% In the case of "continuous S" scans, a delay may be added to take into
% account the acceleration steps
delay_ms = [0,0,0];

% Default orientation of the probe
theta = [-45,atand(1/sqrt(2)),0];
corr = [0,0,0];

% Shift between the electric probe and lidar sensor in cm
lidar_trans_cm = [0.0,-6.8];

% Many booleans (default values)
useMedianFilter       = true;   % apply median filter on images to remove salt&pepper noise
rotateGraph           = false; 	% reverse abscissa and ordinate X<->Y on graphs
showContour           = false; 	% display contour plot containing the isolines of EF components
reprocAll             = true;	% reprocessing raw data saved in *_E_all.csv or use LabVIEW-processed data from *_E_2D.csv
removeBackground      = false;  % If true, a second file path must be specified in "pathBack"
exportGraphicOn       = true;   % Enable/Disable graphics save
useJsonParam.ConvFact = true;   % Use conversion factor from json file
useJsonParam.Offset   = true;   % Use offset correction (no signal) from json file
useJsonParam.Phase    = true;   % Use phase shift correction from json file
useJsonParam.Bgd      = true;   % Use background from json file
useJsonParam.Proj     = true;   % Use background from json file
removeOffsetBorder    = true;   % Remove an additionnal offset using the mean value on the four borders of the image
skipNoiseAnalysis     = true;   % Skip noise analysis step
skipPhaseAnalysis     = true;   % Skip phase analysis step
detectSphere          = false;  % Detect spheres on LIDAR measurement
displayModuleAndPhase = false; %false;  % Display 2 more graphs with module and phase
skipNonProjected      = true;   % Skip display part of non-projected images
shapeRecognition      = true;  % Part under test

% Initialization of some parameters
lidar_range = [];
lidar_profile = {};
caxis_mx = [];
xyz = 'XYZ';
publi = false;

% Part2: : Switch case structure
casename = '221011';
switch casename
    case '240716'
        pathFold = '2024-07-16 Acquisitions Test Projection Angulaire';
        rotateGraph = false;
        shapeRecognition = false;
        jsons = {{1, '240716_165937_cylinder_1000_ydir_imaglabview.json', 'E', 'zlim', [500,20]},
            {2, '240717_141643_Cylinder_1000_ydir_reallabview2_81x243.json', 'E', 'zlim', [400,20]},
            {3, '240704_091158_parallelepipede_pla_10000Hz_ydir+.json', 'E', 'zlim', [400,20]}};
        process=2;

        %% Acquisition la plus récente en haut de la liste
    case '240514'
        pathFold = '2024-05-14 - Acquisitions - Cylindre PLA Publi';
        removeOffsetBorder = true; %false;
        rotateGraph = true;
        jsons = {
            {1, '240514_131221_cylinder_pla_publi.json', 'E', 'zlim', [800,90]}
            };
        % jsons = {
        %     {1 ,'221011_112905_WoodInSand_4kHz.json','E','zlim',[110,20]}
        %     };
        %         useJsonParam.Proj = false;
        %         theta = [0,0,0];
        process = 1; % Si process =1 on analyse le fichier numéro 1

    case '231110'
        pathFold = '2023-11-10 - Acquisitions';
        removeOffsetBorder = true; %false;
        rotateGraph = true;
        jsons = {
            {1, '231110_155950_sphereCalotBleu.json', 'E', 'zlim', [800,90]}
            };
        % jsons = {
        %     {1 ,'221011_112905_WoodInSand_4kHz.json','E','zlim',[110,20]}
        %     };
        %         useJsonParam.Proj = false;
        %         theta = [0,0,0];
        process = 1; % Si process =1 on analyse le fichier numéro 1

    case '221028'
        %%
        pathFold = '2022-10-28 - Acquisitions';
        removeOffsetBorder = true;
        rotateGraph = true;
        jsons = {
            {1, '221028_093443_Default.json', 'E', 'zlim', [110,20]}
            };
        % jsons = {
        %     {1 ,'221011_112905_WoodInSand_4kHz.json','E','zlim',[110,20]}
        %     };
        %         useJsonParam.Proj = false;
        %         theta = [0,0,0];
        process = 1;


        %% Acquisition la plus ancienne en haut de cette liste vers acquision plus récente jusqu'à 221011
    case '210823'
        %%
        % infoE.E = - infoE.E; infoE.I = - infoE.I;
        removeBackground   = true;
        reprocAll = false;
        pathJson_BG = fullfile(pathData,'2021-08-23 - Acquisitions\210823_083522_Background_NoCapaDS.json');
        corr = [+2,8,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-08-23 - Acquisitions';
        jsons = {
            {1,'210823_090052_Triangle_NoCapaDS.json','E','zlim',[1.0,1.0]}
            };
        process = 1;
    case '210823-LIDAR'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [+2,8,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-08-23 - Acquisitions';
        jsons = {
            {1 ,'210823_095302_Triangle_NoCapaDS_withLIDAR.json','EL','zlim',[1.0,1.0]}
            };
        process = 1;
    case '210825'
        %% Source measurements pp, pm, ppmm, ...
        % infoE.E = - infoE.E; infoE.I = - infoE.I;
        phaseEI = [0,0,0];%-[9.7;8.6;1.0]*pi/180; % Correction phase
        corr = [4,8,-16];
        VtoVpm = 1.035*1000/sqrt(2);
        pathFold = '2021-08-24 - Acquisitions';
        removeOffsetBorder    = true;
        skipNoiseAnalysis     = true;
        skipNonProjected      = false;
        jsons = {
            {1 ,'210824_131559_pm.json'      ,'E','zlim',[6.0,1.0]}
            {2 ,'210824_134950_pp.json'      ,'E','zlim',[6.0,1.0]}
            {3 ,'210824_152008_pp.json'      ,'E','zlim',[6.0,1.0]}
            {4 ,'210825_083357_pp.json'      ,'E','publi',true}
            {5 ,'210825_092847_pm.json'      ,'E','zlim',[4.5,0.5]}
            {6 ,'210825_110746_p.json'       ,'E','zlim',[3.2,0.5]}
            {7 ,'210825_132648_ppmm.json'    ,'EL','zlim',[6.0,1.0]}
            {8 ,'210825_142311_pmpm.json'    ,'E','zlim',[4.0,0.5]}
            {9 ,'210825_160754_p2.json'      ,'E','zlim',[4.0,0.5]}
            {10,'210826_084031_p2_z4cm.json' ,'E','zlim',[10.,1.5]}
            };
        process = 5;
        useJsonParam.Proj = false;
        theta = [0,0,0];
        corr = [0,0,0];
    case '210830'
        %%
        % infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,6,-8];
        VtoVpm = 1.035*1000;
        detectSphere = false;
        skipPhaseAnalysis  = false;
        skipNoiseAnalysis  = false;
        pathFold = '2021-08-30 - Acquisitions';
        jsons = {
            {1,'210830_102103_geomI_pmpm_40mm.json','EL','zlim',[6.0,6.0],'delay',[200,80,0]}
            {2,'210830_092707_geomI_ppmm_40mm.json','EL','zlim',[10.,10.],'delay',[200,80,0]}
            };
        process = 1:2;
    case '210902'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        lidar_range = [50,270];
        lidar_profile = {};%{'x30','x40'};
        pathFold = '2021-09-02 - Acquisitions';
        jsons = {
            {1,'210902_103525_AluOnCardbox_Close_ppmm.json','EL','zlim',[4.0,0.5],'delay',[200,80,0]}
            {2,'210902_135733_AluOnCardbox_Open_ppmm.json' ,'EL','zlim',[4.0,0.5],'delay',[200,80,0]}
            {3,'210902_164423_AluOnCardbox_Close_pmmp.json','EL','zlim',[4.0,0.5],'delay',[200,80,0]}
            {4,'210903_090543_AluOnCardbox_Open_pmmp.json' ,'EL','zlim',[4.0,0.5],'delay',[200,80,0]}
            {5,'210903_103234_AluOnCardbox_Open_pmpm.json' ,'E' ,'zlim',[1.5,0.5],'delay',[200,80,0]}
            {6,'210903_164244_AluOnCardbox_Close_pmpm.json','EL','zlim',[1.5,0.5],'delay',[200,80,0]}
            {7,'210903_111815_AluOnCardbox_Close_pmpm.json','E' ,'zlim',[1.5,0.5],'delay',[200,80,0]}
            };
        process = 1:7; % On analyse le fichier 1 à 7
    case '210909'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-09-09 - Acquisitions';
        jsons = {
            {1,'210914_083338_alim_unknown.json' ,'E','zlim',[4.0,1.0],'delay',[200,80,0]};
            {2,'210914_102729_ppmm.json'         ,'E','zlim',[8.0,2.5],'delay',[200,80,0]};
            };
        process = 1:2;
    case '210916'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        skipPhaseAnalysis = true;
        phaseEI = -[40.0;24.2;15.7]*pi/180;
        pathFold = '2021-09-16 - Acquisitions';
        jsons = {
            {1,'210916_151240_ppmm_Z35mm_1.json' ,'E','zlim',[12.,12.],'delay',[200,80,0]}
            {2,'210916_161040_ppmm_Z35mm_2.json' ,'E','zlim',[8.0,8.0],'delay',[200,80,0]}
            {3,'210917_120230_pm_Z35mm.json'     ,'E','zlim',[10.,10.],'delay',[200,80,0]}
            {4,'210920_103758_pm_Z45mm.json'     ,'E','zlim',[6.0,6.0],'delay',[200,80,0]}
            {5,'210920_114917_pm_Z45mm.json'     ,'E','zlim',[6.0,6.0],'delay',[200,80,0]}
            };
        process = 1:5;
    case '210923'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-09-23 - Acquisitions';
        jsons = {
            {1,'210923_124632_ppmm_AgSphere.json' ,'E','zlim',[0.5,0.5]}
            {2,'210924_083641_ppmm_AgSphere.json' ,'E','zlim',[0.4,0.4]}
            };
        process = 1:2;
    case '211006-frequency'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        skipPhaseAnalysis = false;
        pathFold = '2021-10-06 - Acquisitions - Exc. Frequency';
        jsons = {
            {1,'211005_135827_obj_geomI_pm_d60_h40_1kHz.json','E','zlim',[8,8]}
            };
        process = 1;
    case '211006-influence'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-10-06 - Acquisitions - Influence';
        jsons = {
            {1,'211006_111455_Influence_ppmm_SR15_d70_h30.json'          ,'E','zlim',[1.5,1.5]}
            {2,'211006_140431_Influence_ppmm_SR15_d70_h32.json'          ,'E','zlim',[1.5,1.5]}
            {3,'211006_152958_Influence_ppmm_SR15_d70_h34.json'          ,'E','zlim',[1.5,1.5]}
            {4,'211006_164903_Edge.json'                                 ,'E','zlim',[5.0,5.0]}
            {5,'211007_153253_influence_mmpp_metal_sphere_ag_R10_e2.json','E','zlim',[0.5,0.5]}
            };
        process = 1:5;
    case '211011-influence'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        pathJson = fullfile(pathData,'2021-10-11 - Acquisitions - Influence\211011_094016_ppmm_metalCylinder.json'); caxis_mx.E = 1.5; caxis_mx.I = 1.5;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-10-11 - Acquisitions - Influence';
        jsons = {
            {1,'211011_094016_ppmm_metalCylinder.json','E','zlim',[3.0,3.0]}
            };
        process = 1;
    case '211012-influence'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        reprocAll = false;
        useJsonParam.ConvFact = false;
        pathFold = '2021-10-11 - Acquisitions - Influence';
        jsons = {
            {1,'211012_085757_ppmm_metalCylinder_sequential.json','E','zlim',[3.0,3.0]}
            };
        process = 1;
    case '211020'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-2,10,-15];
        VtoVpm = 1.035*1000;
        skipPhaseAnalysis   = false;
        pathFold = '2021-10-20 - Wood-Polystyren';
        jsons = {
            {1,'211020_104325_Wood-Polystyren-500Hz.json','E','zlim',[3.0,3.0]}
            };
        process = 1;
    case '211026'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-4,10,-15];
        VtoVpm = 1.035*1000;
        pathFold = '2021-10-26 - Acquisitions';
        jsons = {
            {1,'211026_105921_ppmm_wood_400Hz.json'      ,'E','zlim',[2.0,0.5]}
            {2,'211026_114618_ppmm_wood_400Hz.json'      ,'E','zlim',[3.0,0.5]}
            {3,'211026_143715_ppmm_metal_cube_400Hz.json','E','zlim',[2.0,0.5]}
            {4,'211026_160621_ppmm_metal_cube_400Hz.json','E','zlim',[2.0,0.5]}
            };
        process = 1:4;
    case '211104'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [-4,10,-15];
        VtoVpm = 1.035*1000;
        removeOffsetBorder  = false;
        pathFold = '2021-11-04 - Acquisitions';
        jsons = {
            {1,'211104_135522_ppmm_wood_400Hz.json'      ,'E','zlim',[5.0,1.5]}
            {2,'211105_130106_pppp_wood_400Hz.json'      ,'E','zlim',[5.0,1.5]}
            };
        process = 1:2;
    case '211117'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [20,-5,17];
        delay_ms = 280*[1,1,1];
        VtoVpm = 6.75*1000;
        pathFold = '2021-11-17 - Acquisitions';
        jsons = {
            {1 ,'211117_102601_new_pm.json'                     ,'E','zlim',[50,7]}
            {2 ,'211117_104512_new_pm_S.json'                   ,'E','zlim',[50,7],'delay',delay_ms}
            {3 ,'211117_151142_new_pm_Sscan.json'               ,'E','zlim',[55,7],'delay',delay_ms}
            {4 ,'211117_153215_new_pm_Sscan_v1000.json'         ,'E','zlim',[50,7],'delay',delay_ms}
            {5 ,'211117_162519_ppmm_metal_cylinder.json'        ,'E','zlim',[8,1],'delay',delay_ms}
            {6 ,'211117_164909_ppmm_teflon_cylinder.json'       ,'E','zlim',[3.5,1],'delay',delay_ms}
            {7 ,'211117_170349_ppmm_metal_cube.json'            ,'E','zlim',[6,1],'delay',delay_ms}
            {8 ,'211122_092435_ppmm_hex_cylinder.json'          ,'E','zlim',[5,1],'delay',delay_ms}
            {9 ,'211122_102556_ppmm_wood_0400Hz.json'           ,'E','zlim',[18,3],'delay',delay_ms}
            {10,'211122_105528_ppmm_wood_1000Hz.json'           ,'E','zlim',[18,3],'delay',delay_ms}
            {11,'211122_112404_ppmm_jar_cover_with_metal.json'  ,'E','zlim',[8,1.5]}
            {12,'211122_114613_ppmm_jar_cover_no_metal.json'    ,'E','zlim',[8,1.5]}
            {13,'211122_134436_ppmm_cover_platic_empty.json'    ,'E','zlim',[14,3.5]}
            {14,'211122_140734_ppmm_flat_metal_cylinder.json'	,'E','zlim',[14,3.5]}
            {15,'211122_153103_ppmm_cover_platic_flat_metal_cylinder.json','E','zlim',[14,3.5]}
            {16,'211123_083643_ppmm_hand.json'                  ,'E','zlim',[14,2.5],'delay',delay_ms,'showContour',1}
            {17,'211123_085027_ppmm_hand.json'                  ,'E','zlim',[14,2.5]}
            {18,'211123_090850_ppmm_hand.json'                  ,'E','zlim',[14,2.5]}
            {19,'211123_092529_ppmm_metal_part.json'            ,'E','zlim',[20,3]}
            {20,'211123_095047_ppmm_hidden_objects.json'        ,'E','zlim',[20,3]}
            {21,'211123_101941_ppmm_hidden_objects.json'        ,'E','zlim',[20,3]}
            {22,'211123_112448_ppmm_torus.json'                 ,'E','zlim',[10,3]}
            {23,'211123_125927_ppmm_torus_w_metal.json'         ,'E','zlim',[10,3]}
            {24,'211122_160533_ppmm_flat_cylinder_wood.json'    ,'E','zlim',[20,3]}
            {25,'211123_133007_ppmm_cetim_materials.json'       ,'E','zlim',[20,3]}
            {26,'211123_135823_ppmm_torus.json'                 ,'E','zlim',[7,1]}
            {27,'211123_144545_ppmm_torus.json'                 ,'E','zlim',[7,1]}
            {28,'211123_150748_ppmm_torus.json'                 ,'E','zlim',[7,1]}
            };
        process = 25;
    case '211124'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        corr = [20,-5,17];
        VtoVpm = 6.75*1000;
        pathFold = '2021-11-24 - Acquisitions';
        jsons = {
            {1 ,'211125_091358_xdir_metal_sphereD15.json'       ,'E','zlim',[5.5,5.5]}
            {2 ,'211125_094518_ydir_metal_sphereD15.json'       ,'E','zlim',[5.5,5.5]}
            {3 ,'211125_102015_quad_metal_sphereD15.json'       ,'E','zlim',[5.5,5.5]}
            {4 ,'211125_104643_quad_metal_part.json'            ,'E','zlim',[10,10]}
            {5 ,'211125_112357_quad_metal_cube.json'            ,'E','zlim',[8,8]}
            {6 ,'211125_115629_quad_metal_cylinder.json'        ,'E','zlim',[8,8]}
            {7 ,'211125_124442_quad_cylinder_bakelite.json'     ,'E','zlim',[8,8]}
            {8 ,'211125_132343_quad_big_empty_metal_box.json'   ,'E','zlim',[12,12]}
            {9 ,'211125_132343_quad_big_empty_metal_box.json'   ,'E','zlim',[12,12]}
            {10,'211125_140856_quad_cup_up.json'                ,'E','zlim',[8,8]}
            {11,'211125_143719_quad_cup_down.json'              ,'E','zlim',[8,8]}
            {12,'211125_150056_quad_big_metal_open_box.json'    ,'E','zlim',[12,12]}
            {13,'211125_154911_quad_book.json'                  ,'E','zlim',[8,8]}
            {14,'211125_163847_quad_big_metal_box_m10mm.json'	,'E','zlim',[5.5,5.5]}
            };
        process = 3;
    case '211206'
        %%
        infoE.E = - infoE.E; infoE.I = - infoE.I;
        phaseEI = [0.12,0.10,0.12] - pi/4;
        useJsonParam.Phase = false;
        corr = [20,-5,17];
        VtoVpm = 6.75*1000;
        rotateGraph = false;
        pathFold = '2021-12-06 - Acquisitions';
        jsons = {
            {1 ,'211206_091007_xdir_bakelite.json'                      ,'E','zlim',[14,14]}
            {2 ,'211206_093149_ydir_bakelite.json'                      ,'E','zlim',[14,14]}
            {3 ,'211206_095121_quad_bakelite.json'                      ,'E','zlim',[14,14]}
            {4 ,'211206_140541_quad_brass_sphere_d15mm_h5mm_cfg1.json'  ,'E','zlim',[5,5]}
            {5 ,'211206_143106_quad_brass_sphere_d15mm_h5mm_cfg2.json'  ,'E','zlim',[3.5,3.5]}
            {6 ,'211206_154141_quad_brass_sphere_d15mm_h10mm_cfg2.json' ,'E','zlim',[2,2]}
            {7 ,'211206_170905_quad_steel_sphere_d8mm_h2mm_cfg2.json'   ,'E','zlim',[0.7,0.7]}
            };
        process = 2;
    case '211209'
        %%
        theta = [-atand(1/sqrt(2)),45,0];
        corr = [4,-4,8];
        VtoVpm = 7.7 * 1000;
        pathFold = '2021-12-09 - Acquisitions - v2b';
        rotateGraph = true;
        jsons = {
            {1 ,'211209_160631_v2b_nc_dipolar_d60_h25.json'         ,'E','zlim',[45.,45.]}
            {2 ,'211210_110710_v2b_nc_quad_d70_brass_sphere.json'	,'E','zlim',[5.0,5.0]}
            {3 ,'211210_152636_v2b_nc_xdir_d70_noObject.json'       ,'E','zlim',[6.0,6.0]}
            {4 ,'211210_145509_v2b_nc_xdir_d70_hiddenBakelite.json' ,'E','zlim',[6.0,6.0]}
            {5 ,'211210_155847_v2b_nc_quad_d70_noObject.json'       ,'E','zlim',[3.5,3.5]}
            {6 ,'211210_143123_v2b_nc_quad_d70_hiddenBakelite.json' ,'E','zlim',[3.5,3.5]}
            {7 ,'211213_101350_v2b_nc_xdir_d70_hiddenObject.json'   ,'E','zlim',[4.0,4.0]}
            {8 ,'211213_104913_v2b_nc_xdir_d70_noObject.json'       ,'E','zlim',[4.0,4.0]}
            {9 ,'211213_153004_v2b_nc_xdir_d70_metalCylinder.json'  ,'E','zlim',[20.,20.]}
            {10,'211213_164343_v2b_nc_xdir_d70_steel_sphere_d8.json','E','zlim',[1.0,1.0]}
            };
        process = 8;
    case '211214'
        %%
        rotateGraph  = true;
        theta = [-atand(1/sqrt(2)),45,0];
        corr = [4,-4,8];
        VtoVpm = 7.7 * 1000;
        pathFold = '2021-12-14 - Acquisitions';
        jsons = {
            {1 ,'211214_145044_v2b_nc_xdir_d70_chicken_1.json'      ,'E','zlim',[11.,1.0]}
            {2 ,'211214_150709_v2b_nc_xdir_d70_chicken_2.json'      ,'E','zlim',[12.,1.0]}
            {3 ,'211214_152337_v2b_nc_xdir_d70_chicken_3.json'      ,'E','zlim',[18.,1.0]}
            {4 ,'211215_104649_v2b_nc_xdir_d70_edge_metal.json'     ,'E','zlim',[10.,10.]}
            {5 ,'211215_111821_v2b_nc_ydir_d70_edge_metal.json'     ,'E','zlim',[10.,10.]}
            {6 ,'211215_145949_v2b_nc_ydir_d52_edge_metal.json'     ,'E','zlim',[11.,11.]}
            };
        process = 1:6;
    case '220110'
        %%
        theta = [-atand(1/sqrt(2)),45,0];
        corr = [4,-4,8];
        detectSphere = true;
        pathFold = '2022-01-10 - SOP';
        jsons = {
            {1 ,'220110_121046_SOP-example.json' ,'EL','zlim',[35.,35.]}
            };
        process = 1;
    case '220126'
        %%
        theta = [-atand(1/sqrt(2)),45,0];
        corr = [4,-4,8];
        pathFold = '2022-01-26 - Acquisitions';
        displayModuleAndPhase = true;
        removeOffsetBorder    = false;
        jsons = {
            {1 ,'220126_161547_v2b_GeomI_r15.json' ,'E','zlim',[130,130]}
            {2 ,'220126_165019_v2b_hiddenObject.json' ,'E','zlim',[280,30]}
            {3 ,'220127_093932_v2b_xdir_hiddenObject_glassCover.json' ,'E','zlim',[150,30]}
            {4 ,'220127_104526_v2b_xdir_noHiddenObject.json' ,'E','zlim',[150,30]}
            {5 ,'220127_110644_v2b_xdir_hiddenObject_metal_bottom.json' ,'E','zlim',[150,30]}
            {6 ,'220127_112807_v2b_xdir_hiddenObject_plasticMold.json' ,'E','zlim',[150,30]}
            {7 ,'220127_161653_v2b_cage_ydir.json' ,'E','zlim',[400,30]}
            {8 ,'220128_130956_v2b_cage_ydir.json' ,'E','zlim',[400,30]}
            {9 ,'220128_132150_v2b_cage_ydir_sidefree.json' ,'E','zlim',[400,30]}
            {10,'220131_141654_v2b_cage_ydir_sidefree.json' ,'E','zlim',[400,30]}
            {11,'220131_142636_v2b_cage_ydir_sidelock.json' ,'E','zlim',[400,30]}
            {12,'220131_145004_v2b_cage_ydir_sidelock_tableGrounded.json' ,'E','zlim',[400,30]}
            };
        process = 12;
    case '220201'
        %%
        theta = [-atand(1/sqrt(2)),45,0];
        corr = [1.8,-11.5,-7];
        pathFold = '2022-02-01 - Acquisitions';
        removeOffsetBorder    = true;
        useJsonParam.Proj     = true;
        jsons = {
            {1,'220201_131240_v2b_cage_ydir_sidelock_tableGrounded.json' ,'E','zlim',[800,30]}
            {2,'220201_160309_v2b_cage_ydir_sidefree.json' ,'E','zlim',[350,30],'zoffset',true}
            {3,'220201_161223_v2b_cage_ydir_sidelock.json' ,'E','zlim',[350,30],'zoffset',true}
            {4,'220201_162246_v2b_cage_ydir_sidelock_sphere.json' ,'E','zlim',[400,400],'bg','220201_161223_v2b_cage_ydir_sidelock.json'}
            };
        process = 3;
    case '220209'
        %%
        pathFold = '2022-02-09 - Acquisitions';
        removeOffsetBorder    = false;
        useJsonParam.Offset   = true;
        useJsonParam.Proj     = true;
        skipPhaseAnalysis     = true;
        useJsonParam.Phase    = true;
        %         phaseEI = [0,0,0];
        jsons = {
            {1,'220209_124010_v2b_sphere_p.json' ,'E','zlim',[450,70]}
            {2,'220209_131611_v2b_sphere_p_vext.json' ,'E','zlim',[450,70]}
            {3,'220210_115640_v2b_sphere_p_vext_E_noMetalStage.json' ,'E','zlim',[450,70]}
            {4,'220210_163534_v2b_sphere_p_vext_E_noMetalStage_nonCroisé.json' ,'E','zlim',[450,70]}
            {5,'220211_132315_v2b_sphere_p_VextB.json' ,'E','zlim',[450,70],'bg','220211_135842_v2b_sphere_p_VextB_noexc.json'}
            {6,'220211_135842_v2b_sphere_p_VextB_noexc.json' ,'E','zlim',[45,7]}
            {7,'220211_144251_v2b_sphere_p_VextB_shielded.json' ,'E','zlim',[450,70]}
            {8,'220211_152500_v2b_sphere_p_VextB_shielded_x2.json' ,'E','zlim',[450,70]}
            };
        process = 1;
    case '220214'
        %% Buried objects measurement
        pathFold = '2022-02-14 - Acquisitions';
        removeOffsetBorder    = true;
        rotateGraph           = true;
        skipPhaseAnalysis     = true;
        shapeRecognition      = true;
        jsons = {
            {1,'220214_152746_v2b_sand_plastic.json' ,'E','zlim',[120,40]}
            {2,'220214_160108_v2b_sand_plastic_10mm.json' ,'E','zlim',[120,40]}
            {3,'220215_155847_v2b_sand_metal_surface.json' ,'E','zlim',[120,40]}
            {4,'220216_154859_v2b_sand_plastic_surface.json' ,'E','zlim',[120,30],'zoffset',1}
            {5,'220216_161839_v2b_sand_plastic_4mm.json' ,'E','zlim',[120,15],'zoffset',1}
            {6,'220217_142031_v2b_sand_plastic_4mm.json' ,'E','zlim',[120,15],'zoffset',1}
            {7,'220217_144655_v2b_sand_plastic_4mm_10khz.json' ,'E','zlim',[40,20],'zoffset',1}
            {8,'220217_151921_v2b_sand_plastic_4mm_20khz.json' ,'E','zlim',[20,10],'zoffset',1}
            {9,'220222_160813_v2b_sand_plastic_3mm_2khz.json' ,'E','zlim',[120,50],'zoffset',1,'shape'}
            {10,'220222_170238_v2b_sand_plastic_7mm_2khz.json' ,'E','zlim',[60,20],'zoffset',1}
            {11,'220223_091356_v2b_sand_plastic_12mm_2khz.json' ,'E','zlim',[40,12],'zoffset',1}
            {12,'220223_132904_v2b_sand_plastic_20mm_2khz.json' ,'E','zlim',[40,12],'zoffset',1}
            {13,'220223_143934_v2b_sand_wood_2khz_3mm.json' ,'E','zlim',[40,25],'zoffset',1,'shape'}
            {14,'220224_161210_v2b_sand_plasticbottle_10khz_5mm.json' ,'E','zlim',[20,10],'zoffset',1,'shape'}
            {15,'220321_130004_v2b_sand_plasticbottle_huile_4khz.json' ,'E','zlim',[4,1.5],'zoffset',1}
            };
        process = 13;
    case '220509'
        %%
        pathFold = '2022-05-09 - Acquisitions';
        removeOffsetBorder    = true;
        rotateGraph           = true;
        skipPhaseAnalysis     = true;
        jsons = {
            {1,'220509_095137_ThreePlateSamples_01.json' ,'E','zlim',[120,1]}
            {2,'220509_110613_ThreePlateSamples_02.json' ,'E','zlim',[120,1]}
            {3,'220509_120147_ThreePlateSamples_03.json' ,'E','zlim',[80,20]}
            };
        process = 2;
    case '220519'
        %%
        pathFold = '2022-05-19 - Acquisitions';
        %         removeOffsetBorder    = true;
        skipPhaseAnalysis     = true;
        useMedianFilter = true;
        jsons = {
            {1,'220519_095950_Magn.json' ,'M','zlim',[120,1],'bg','220519_102525_Magn_back.json'}
            };
        process = 1;
    case '220520'
        %%
        pathFold = '2022-05-20 - Acquisitions';
        %         removeOffsetBorder    = true;
        skipPhaseAnalysis     = true;
        jsons = {
            {1,'220523_091257_Coil01_Star_AlimON_400mA.json' ,'M','bg','220523_094446_Coil01_Star_AlimOFF.json','Bparam',{1,'SSA'}}
            {2,'220523_103108_Coil02_Donut_AlimON_400mA.json' ,'M','bg','220523_094446_Coil01_Star_AlimOFF.json','Bparam',{-1,'SSA'}}
            {3,'220523_111317_Coil03_Classic_AlimON_400mA.json' ,'M','bg','220523_094446_Coil01_Star_AlimOFF.json','Bparam',{1,'SSA'}}
            {4,'220525_085852_SphereMagnet.json' ,'M','bg','220525_094648_SphereMagnet_BG.json','Bparam',{1,'SSA'}}
            {5,'220525_103941_SphereMagnet_pos2.json' ,'M','bg','220525_094648_SphereMagnet_BG.json','Bparam',{1,'SSA'}}
            {6,'220523_094446_Coil01_Star_AlimOFF.json' ,'M'}
            };
        process = 5;
    case '220530'
        %%
        pathFold = '2022-05-30 - Acquisitions';
        removeOffsetBorder    = true;
        rotateGraph           = true;
        jsons = {
            {1,'220530_135100_PlasticBottle_ydir_5k.json' ,'E','zlim',[5,2],'zoffset',1,'shape'}
            {2,'220530_161611_Claw_ydir_5k.json' ,'E','zlim',[5,2],'zoffset',1,'shape'}
            {3,'220530_164149_Claw_ydir_5k.json' ,'E','zlim',[5,2],'zoffset',1,'shape'}
            };
        process = 3;
    case '220603'
        %%
        pathFold = '2022-06-03 - Acquisitions';
        removeOffsetBorder    = true;
        rotateGraph           = true;
        jsons = {
            {1 ,'220603_091512_Rice_twobobject_ydir_5k.json' ,'E', 'zlim',[60,1.0]}
            {2 ,'220603_105414_Rice_5k_metal_surface.json' ,'E', 'zlim',[55.0,1.0]};%,'bg','220603_104134_Rice_5k_bg.json', 'zlim',[1.5,0.2]}
            {3 ,'220603_113433_Rice_5k_plastic_sphere.json','E','zlim',[30,0.8]}
            {4 ,'220603_122145_Rice_5k_plastic_sphere_cover_platic.json','E','zlim',[20,0.4]}
            {5 ,'220603_123227_Rice_5k_plastic_sphere_cover_platic_flipped.json','E','zlim',[20,0.4]}
            {6 ,'220603_124509_Rice_5k_plastic_sphere_cover_platic_flipped_xdir.json','E','zlim',[20,0.4]}
            {7 ,'220603_133657_RiceBox_5k_objets_ydir.json','E','zlim',[20,0.4]}
            {8 ,'220603_134455_RiceBox_5k_objets_xdir.json','E','zlim',[20,0.4]}
            {9 ,'220603_135900_RiceBox_5k_objets_xdir_flipud.json','E','zlim',[20,0.4]}
            {10,'220603_140842_RiceBox_5k_objets_ydir_flipud.json','E','zlim',[20,0.4]}
            {11,'220603_104134_Rice_5k_bg.json' ,'E', 'zlim',[55.0,1.0]}
            {12,'220603_105414_Rice_5k_metal_surface.json' ,'E', 'bg','220603_104134_Rice_5k_bg.json', 'zlim',[1.5,0.2]}
            };
        process = 2;
    case '220729'
        %%
        pathFold = '2022-07-29 - Acquisitions';
        removeOffsetBorder    = true;
        jsons = {
            {1 ,'220729_101448_safran_2_m01.json','E'}
            {2 ,'220729_103719_safran_2_m02.json','E'}
            {3 ,'220729_114910_safran_2_m04.json','E'}
            {4 ,'220729_150841_safran_2_m05.json','E'}
            {5 ,'220729_151728_safran_3_m01.json','E'}
            };
        process = 5;
    case '220901'
        %%
        pathFold = '2022-09-01 - Acquisitions';
        removeOffsetBorder    = false;
        rotateGraph = true;
        jsons = {
            {1 ,'220831_100603_Rice_MetalSphere10mm.json','E'}
            {2 ,'220831_102123_Rice_PlasticPlate.json','E'}
            {3 ,'220831_103308_Rice_PlasticPlate2.json','E'}
            {4 ,'220831_110332_Rice_PlasticPlate3.json','E'}
            {5 ,'220831_111544_PlasticPlate.json','E'}
            {6 ,'220831_112218_MetalSphere.json','E'}
            {7 ,'220831_112933_MetalSphere1kHz.json','E'}
            {8 ,'220831_113601_MetalSphere1kHz_2.json','E'}
            {9 ,'220831_114258_PlasticPlate1kHz.json','E'}
            {10,'220831_133616_PlasticPlateAndRice1kHz.json','E'}
            {11,'220901_094444_frozenRiceWithPlasticObject10kHz.json','E'}
            {12,'220901_095329_frozenRiceWithPlasticObject10kHz.json','E'}
            {13,'220901_100107_frozenRiceWithPlasticObject50kHz.json','E'}
            };
        process = 10;
    case '220922'
        %%
        pathFold = '2022-09-22 - Acquisitions';
        removeOffsetBorder = true;
        rotateGraph = true;
        jsons = {
            {1 ,'220922_134555_wood_in_sand.json','E','zlim',[0.7,0.2]}
            {2 ,'220922_164319_wood_in_sand.json','E','zlim',[6.0,2.0]}
            {3 ,'220922_171645_wood_in_sand.json','E','zlim',[6.0,2.0]}
            {4 ,'220923_090534_wood_in_sand_x.json','E','zlim',[5.0,2.0]}
            {5 ,'220923_092939_bone_in_sand_x.json','E','zlim',[5.0,0.2]}
            {6 ,'220923_094601_bone_in_sand_y.json','E','zlim',[5.0,0.1]}
            {7 ,'220923_111618_bone_in_sand_x_10khz.json','E','zlim',[5.0,0.1]}
            {8 ,'220923_113656_bone_in_sand_x_5khz.json','E','zlim',[5.0,0.3]}
            {9 ,'220923_144446_bone_in_sand_x_950hz_closer1cm.json','E','zlim',[12.0,0.5]}
            {10,'220923_150210_bottlewater_in_sand_x_950hz.json','E','zlim',[12.0,0.6]}
            {11,'220923_161149_flatplasticbag_in_sand_x_950hz.json','E','zlim',[12.0,1.0]}
            {12,'220923_162956_flatplasticbag_in_sand_x_950hz_smaller.json','E','zlim',[10.0,0.6]}
            {13,'220923_164535_verticalbigplasticbag_in_sand_x_950hz.json','E','zlim',[5.0,0.6]}
            {14,'220923_170207_flatbigplasticbag_in_sand_x_950hz.json','E','zlim',[5.0,1.0]}
            };
        process = 11;
    case '221011'
        %%
        pathFold = '2022-10-11 - Acquisitions';
        removeOffsetBorder = true;
        rotateGraph = true;
        jsons = {
            {1 ,'221011_112905_WoodInSand_4kHz.json','E','zlim',[110,20]}
            {2 ,'221011_120946_Sand_4kHz.json','E','zlim',[110,20]}
            {3 ,'221011_112905_WoodInSand_4kHz.json','E','zlim',[110,20],'bg','221011_120946_Sand_4kHz.json'}
            {4 ,'221011_114940_PlasticBagInSand_4kHz.json','E','zlim',[10,5],'bg','221011_120946_Sand_4kHz.json'}
            {5 ,'221011_152552_Sand_4kHz_Ex.json','E','zlim',[110,20]}
            {6 ,'221011_154152_PlasticBagInSand_4kHz_Ex.json','E','zlim',[30,15],'bg','221011_152552_Sand_4kHz_Ex.json'}
            {7 ,'221011_160531_SandMixed_4kHz_Ex.json','E','zlim',[110,5]}
            {8 ,'221011_163409_PlasticBagInSandMixed_4kHz_Ex.json','E','zlim',[110,5]}
            {9 ,'221012_095004_SandMixed_4kHz_Ex.json','E','zlim',[110,5]}
            {10,'221012_101641_PlasticBagInSandMixed_4kHz_Ex.json','E','zlim',[110,5]}
            {11,'221012_103441_PlasticBagBInSandMixed_4kHz_Ex.json','E','zlim',[110,5]}
            };
        %         useJsonParam.Proj = false;
        %         theta = [0,0,0];
        process = 1;
    otherwise
        cprintf(colors{3},"No case named '%s' found in SWITCH CASE structure. ABORT",casename);cprintf('white',"\n");
        return
end

%% Display info to console
fprintf(" \n-> Configuration: ");cprintf(colors{2},"%s\n",casename)
fprintf("Conversion factors:\n")
fprintf("1inc  = ");cprintf(colors{4},"%8.5f mm\n",incToMm);
if sum(abs(corr))>0
    fprintf("Projection angles corrections:");cprintf(colors{4},"%4.0f°(X) %4.0f°(Y)  %4.0f°(Z)\n",corr);
end
fprintf("Steps:\n")
fprintf("  Remove background      ? ");cprintf(colors{5},"%3s",todo(removeBackground));cprintf('white',"\n");
fprintf("  Reprocess 2D images    ? ");cprintf(colors{5},"%3s",todo(reprocAll));cprintf('white',"\n");
fprintf("  Remove offset          ? ");cprintf(colors{5},"%3s",todo(removeOffsetBorder));cprintf('white',"\n");
fprintf("  Use median filter      ? ");cprintf(colors{5},"%3s",todo(useMedianFilter));cprintf('white',"\n");
fprintf("  Detect spheres (LIDAR) ? ");cprintf(colors{5},"%3s",todo(detectSphere));cprintf('white',"\n");
fprintf("  Noise analysis         ? ");cprintf(colors{5},"%3s",todo(~skipNoiseAnalysis));cprintf('white',"\n");
fprintf("  Phase analysis         ? ");cprintf(colors{5},"%3s",todo(~skipPhaseAnalysis));cprintf('white',"\n");
fprintf("  Export graphics to JPG ? ");cprintf(colors{5},"%3s",todo(exportGraphicOn));cprintf('white',"\n");
fprintf("  Display Modul/Phase?   ? ");cprintf(colors{5},"%3s",todo(displayModuleAndPhase));cprintf('white',"\n");

fprintf("Data path:\n"); cprintf(colors{2},"    %s",pathFold);cprintf('white'," \n");
fprintf("Filename:\n")
njson = length(process);
for i = 1 : njson
    fprintf("    %02i  ",i); cprintf(colors{2},"%s",jsons{process(i)}{2});cprintf('white'," \n");
end
if removeBackground
    fprintf("Data path for background:\n"); cprintf(colors{2},"    %s",pathJson_BG);cprintf('white'," \n");
end
%% Start analysis main loop
for n = 1 : njson
    close all
    jsonname    = jsons{process(n)}{2};
    pathJson = fullfile(pathData,pathFold,jsonname);
    fields      = jsons{process(n)}{3};

    % Get parameters from jsons array
    isParam = find(strcmp(jsons{process(n)},'zlim'));
    if isParam
        caxis_mx.E = jsons{process(n)}{isParam+1}(1);
        caxis_mx.I = jsons{process(n)}{isParam+1}(2);
    else
        caxis_mx = [];
    end
    isParam = find(strcmp(jsons{process(n)},'zoffset'));
    if isParam
        zoffset = jsons{process(n)}{isParam+1}(1);
    else
        zoffset = 0;
    end
    isParam = find(strcmp(jsons{process(n)},'delay'));
    if isParam
        delay_ms = jsons{process(n)}{isParam+1};
    else
        delay_ms = [0,0,0];
    end
    isParam = find(strcmp(jsons{process(n)},'showContour'));
    if isParam
        showContour = jsons{process(n)}{isParam+1};
    else
        showContour = 0;
    end
    isParam = find(strcmp(jsons{process(n)},'bg'));
    if isParam
        removeBackground = true;
        pathJson_BG = fullfile(pathData,pathFold,jsons{process(n)}{isParam+1});
    else
        removeBackground = false;
    end
    isParam = find(strcmp(jsons{process(n)},'publi'));
    if isParam
        publi = true;
    end
    isParam = find(strcmp(jsons{process(n)},'shape'));
    if isParam
        shapeRecognition = true;
    end
    isParam = find(strcmp(jsons{process(n)},'Bparam'));
    if isParam
        bparam = jsons{process(n)}{isParam+1};
    else
        bparam = {1,'SSS'}; % sign, S: Symetric A: Asymetric
    end

    [jsonpath,~,~] = fileparts(pathJson);
    pathSave = fullfile(jsonpath,'processing');
    if ~exist(pathSave,'dir'),mkdir(pathSave);end
    fprintf('\nFILE %02i/%02i: ',n,njson);cprintf(colors{2},"%s",jsonname);cprintf('white',"\n");

    % Get background paths
    pathE = strrep(pathJson,'.json','_E_2D.csv');
    pathB = strrep(pathJson,'.json','_B_2D.csv');
    if removeBackground
        if exist(pathJson_BG,'file')
            pathE_BG = strrep(pathJson_BG,'.json','_E_2D.csv');
            pathB_BG = strrep(pathJson_BG,'.json','_B_2D.csv');
        else
            cprintf(colors{3},"/!\\ Background not found, continue anyway");cprintf('white',"\n");
            removeBackground = false;
            fprintf("  Remove background      ? ");cprintf(colors{5},"%3s",todo(removeBackground));cprintf('white',"\n");
        end
    end

    % Load parameters from JSON files
    if ~exist(pathJson,'file')
        cprintf(colors{3},"%s","Json file not found - ABORT");cprintf('white',"\n");
        cprintf(colors{2},"%s",pathJson);cprintf('white',"\n");
        return
    end
    J = loadjson(pathJson);
    acquiOffset = J.offset.data;
    dim = [J.scan_xy.x_nb,J.scan_xy.y_nb];
    limx = [J.scan_xy.x_min,J.scan_xy.x_max];
    limy = [J.scan_xy.y_min,J.scan_xy.y_max];
    mode = J.scan_xy.Mode;

    % Set x and y used for acquisition in mm
    xinc = linspace(limx(1),limx(2),dim(1));
    yinc = linspace(limy(1),limy(2),dim(2));
    xcm = incToMm * xinc /10; %Transformation of xinc to xmm and to xcm with /10 --> Position x of the data points for acquisition scan
    ycm = incToMm * yinc /10; %Transformation of yinc to ymm and to ycm with /10 --> Position y of the data points for acquisition scan

    %% GET DATA FROM ACQUISITION FILES
    fprintf('-> Get data:\n');
    procE = contains(fields,'E') | contains(fields,'I');
    if procE %Do we Process E?
        if reprocAll %Do we process raw data ? Else we use data processed in labview
            pathEall = strrep(pathJson,'.json','_E_all.csv');
            [dataE,yi] = ReprocData(pathEall,'EI',infoE,limy,mode,delay_ms); % dataE contains dataE.E = Ereal and dataE.I = Eimag --> Ereal(y=n, x=p,:) = [Ex(x,y), Ey(x,y), Ez(x,y)]
            yEcm = incToMm * yi /10;
        else
            dataE = GetData(pathE,'EI',infoE,dim);
            yEcm = ycm;
        end

        if removeBackground
            if reprocAll
                pathEall = strrep(pathJson_BG,'.json','_E_all.csv');
                [dataE_BG ,yi] = ReprocData(pathEall,'EI',infoE,limy,mode,delay_ms,length(yi));
            else
                dataE_BG  = GetData(pathE_BG,'EI',infoE,dim);
                yEcm = ycm;
            end
        end
    end

    procB = contains(fields,'M') | contains(fields,'A') | contains(fields,'G') | contains(fields,'L');
    if procB
        if reprocAll
            pathBall = strrep(pathJson,'.json','_B_all.csv');
            [dataB,yi] = ReprocData(pathBall,'MAGL',infoM,limy,mode,delay_ms);
            yBcm = incToMm * yi /10;
        else
            dataB = GetData(pathB,'MAGL',infoM,dim);
            yBcm = ycm;
        end
        if isempty(dataB), fprintf('Processing stopped\n'); return; end
        if removeBackground
            if reprocAll
                pathBall = strrep(pathJson_BG,'.json','_B_all.csv');
                [dataB_BG ,yi] = ReprocData(pathBall,'MAGL',infoM,limy,mode,delay_ms,length(yi));
            else
                dataB_BG  = GetData(pathB_BG,'MAGL',infoE,dim);
                yBcm = ycm;fi
            end
        end
    end

    %% Post-processing
    for i = 1 : length(fields)
        fi = fields(i);
        if strcmp(fi,'E')
            cprintf(colors{7},'\n-> Field: %c',fi);cprintf('white',"\n");
            nfi = length(infoE.(fi));
            ycm = yEcm;

            %% Get signal potential applied on sources
            if isfield(J,'Vpp')
                Vamp = J.Vpp / 2;
                fprintf("o) Signal Excitation amplitude: ");cprintf(colors{4}," %3.1f V\n",Vamp);
            end

            %% Remove background measurement
            fprintf("o) Remove background measurement: ")
            if removeBackground    % Did we made a scan without any object to have a background E-field local to each point of the scan ? Considering it does not vary a lot between both acquisitions
                ereal = (dataE.E - dataE_BG.E);
                eimag = (dataE.I - dataE_BG.I);
                cprintf(colors{6},"done\n");
            else
                ereal = dataE.E;
                eimag = dataE.I;
                cprintf(colors{5},"none\n");
            end

            %% Get conversion factor from V to V/m
            fprintf("o) Apply conversion factor: ")
            VtoVpmField = VtoVpm; %Conversion factor, acquisition is in Volts but represent a measurement in V/m
            VtoVpmCalib = VtoVpm;
            if reprocAll
                if useJsonParam.ConvFact
                    if isfield(J,'VtoVpm')
                        VtoVpmField = J.VtoVpm;
                        VtoVpmCalib = 1;
                        cprintf(colors{1},"from json file\n");
                    else
                        cprintf(colors{3},"not found in json "); cprintf(colors{8},"from matlab\n");
                    end
                else
                    cprintf(colors{8},"from matlab\n");
                end
            else
                cprintf(colors{8},"from matlab\n");
            end
            cprintf(colors{4},"         %3.1f (V/m)/V\n",VtoVpmField);
            ereal = VtoVpmField * ereal;
            eimag = VtoVpmField * eimag;

            %% Remove offset
            fprintf("o) Correct offsets (no signal): ")
            offset.E = reshape(offsetE,length(offsetE),1);
            offset.I = reshape(offsetI,length(offsetI),1);
            if reprocAll
                if useJsonParam.Offset
                    if isfield(J,'offset')
                        offset.E = sign(infoE.E)'.* VtoVpmCalib .* [J.offset.data.rx;J.offset.data.ry;J.offset.data.rz];
                        offset.I = sign(infoE.I)'.* VtoVpmCalib .* [J.offset.data.ix;J.offset.data.iy;J.offset.data.iz];
                        cprintf(colors{1},"from json file\n");
                    else
                        cprintf(colors{3},"not found in json "); cprintf(colors{8},"from matlab\n");
                    end
                else
                    cprintf(colors{8},"from matlab\n");
                end
                fprintf("(real)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",offset.E);
                fprintf("(imag)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",offset.I);
                offset3 = permute(repmat(offset.E,[1,size(ereal,1:2)]),[2,3,1]);%Repetition of phase value for each point and permutation to have compatible dimensions
                % Example a = [ [1,2,3] ; [4,5,6]; [7,8,9]]; permute(a, [2,1]) --> a = [ [1,4,7] ; [2,5,8]; [3,6,9]]
                % Here, first dimension is assigned to last, 2nd is
                % assigned to 1st and 3rd is assigned to 2nd.
                ereal = ereal - offset3;  %Substraction of offset for Ereal
                offset3 = permute(repmat(offset.I,[1,size(eimag,1:2)]),[2,3,1]);
                eimag = eimag - offset3; %Substraction of offset for Eimag
            else
                cprintf(colors{5},"skipped\n");
            end

            %% Correct phase shifts --> Excitation on, far from objet i.e no imaginary part at this stage
            fprintf("o) Correct phase shifts: ")
            phase = reshape(phaseEI,length(phaseEI),1);
            if reprocAll
                if useJsonParam.Phase
                    if isfield(J,'phase')
                        phase = [J.phase.data.rx;J.phase.data.ry;J.phase.data.rz];
                        cprintf(colors{1},"from json file\n");
                    else
                        cprintf(colors{3},"not found in json "); cprintf(colors{8},"from matlab\n");
                    end
                else
                    cprintf(colors{8},"from matlab\n");
                end

                cprintf(colors{4},"      %7.2f(X)%7.2f(Y)%7.2f(Z) [rad]\n",phase); % Print information to Console

                phase3 = permute(repmat(phase,[1,size(eimag,1:2)]),[2,3,1]); %Repetition of phase value for each point and permutation to have compatible dimensions
                % Example a = [ [1,2,3] ; [4,5,6]; [7,8,9]]; permute(a, [2,1]) --> a = [ [1,4,7] ; [2,5,8]; [3,6,9]]
                z = ereal + 1i*eimag; %Combination into a complex number to then apply phase transformation
                ereal = real(z.*exp(-1i*phase3)); % Apply phase shift to Ereal
                eimag = imag(z.*exp(-1i*phase3)); % Apply phase shift to Eimag
            else
                cprintf(colors{5},"skipped\n");
            end

            %% Remove background signal --> No excitation, Far from Object
            fprintf("o) Remove background signal: ")
            bgd.E = reshape(bgdE,length(bgdE),1);
            bgd.I = reshape(bgdI,length(bgdI),1);
            if reprocAll
                if useJsonParam.Bgd
                    if isfield(J,'bg')
                        bgd.E = sign(infoE.E)'.* VtoVpmCalib .* [J.bg.data.rx;J.bg.data.ry;J.bg.data.rz];
                        bgd.I = sign(infoE.I)'.* VtoVpmCalib .* [J.bg.data.ix;J.bg.data.iy;J.bg.data.iz];

                        %Display Information To Console
                        cprintf(colors{1},"from json file\n");
                    else
                        %Display Information To Console
                        cprintf(colors{3},"not found in json "); cprintf(colors{8},"from matlab\n");
                    end
                else
                    cprintf(colors{8},"from matlab\n");
                end
                
                %Display Information To Console
                fprintf("(real)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",bgd.E);
                fprintf("(imag)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",bgd.I);

                % Background Value Replicated in Table with compatible
                % dimensions
                bgd3 = permute(repmat(bgd.E,[1,size(ereal,1:2)]),[2,3,1]);
                ereal = ereal - bgd3; %Substration of Background Signal for Ereal
                bgd3 = permute(repmat(bgd.I,[1,size(ereal,1:2)]),[2,3,1]);
                eimag = eimag - bgd3; %Substration of Background Signal for Eimag
            else
                %Display Information To Console
                cprintf(colors{5},"skipped\n");
            end

            %% Remove the mean value from border
            % Display info to console
            fprintf("o) Remove offset from image border: ");
            if removeOffsetBorder % If spatial dimension of scan is large enough, border should contain informations on background
                % For real part
                offsetBord.E = mean([squeeze(mean(ereal(1,:,:))),squeeze(mean(ereal(end,:,:))),squeeze(mean(ereal(:,1,:))),squeeze(mean(ereal(:,end,:)))],2);
                % For Imaginary part
                offsetBord.I = mean([squeeze(mean(eimag(1,:,:))),squeeze(mean(eimag(end,:,:))),squeeze(mean(eimag(:,1,:))),squeeze(mean(eimag(:,end,:)))],2);
                % Real part : Creation of table containing offset value with compatible dimension : each axis and each point
                off3 = permute(repmat(offsetBord.E,[1,size(ereal,1:2)]),[2,3,1]);
                % REAL PART : SUBSTRACTION OPERATION
                ereal = ereal - off3;
                % Imaginary part : Creation of table containing offset value with compatible dimension : each axis and each point
                off3 = permute(repmat(offsetBord.I,[1,size(ereal,1:2)]),[2,3,1]);
                % Imaginary part : Substraction operation
                eimag = eimag - off3;

                %Display Information To Console
                fprintf("\n");
                fprintf("(real)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",offsetBord.E);
                fprintf("(imag)");cprintf(colors{4},"%7.2f(X)%7.2f(Y)%7.2f(Z) [V/m]\n",offsetBord.I);
            else%Display Information To Console
                cprintf(colors{5},"skipped\n");
            end

            %% GET PROJECTION ANGLES FROM JSON
            %Display Information To Console
            fprintf("o) Get projection angles: ");

            % DEFINITION OF ANGLES IN CASE NOT CONTAINED IN JSON
            thx = theta(1) + corr(1);
            thy = theta(2) + corr(2);
            thz = theta(3) + corr(3);

            if reprocAll
                if useJsonParam.Proj
                    if isfield(J,'angProj')
                        % DEFINITION OF ANGLES IF CONTAINED IN JSON
                        thx = J.angProj.data.rx;
                        thy = J.angProj.data.ry;
                        thz = J.angProj.data.rz;
                        %Display Information To Console
                        cprintf(colors{1},"from json file\n");
                    else%Display Information To Console
                        cprintf(colors{3},"not found in json "); cprintf(colors{8},"from matlab\n");
                    end
                else%Display Information To Console
                    cprintf(colors{8},"from matlab\n");
                end

                %Display Information To Console
                fprintf("%cx:",952);cprintf(colors{4},"%6.1f° +%6.1f°\n",theta(1),thx-theta(1));
                fprintf("%cy:",952);cprintf(colors{4},"%6.1f° +%6.1f°\n",theta(2),thy-theta(2));
                fprintf("%cz:",952);cprintf(colors{4},"%6.1f° +%6.1f°\n",theta(3),thz-theta(3));
            else%Display Information To Console
                cprintf(colors{5},"skipped\n");
            end
            %% DISPLAY NOISE IMAGES BASED ON MEDIAN FILTER
            % Display Information To Console
            fprintf("o) Noise analysis: ");
            if ~skipNoiseAnalysis % IF NOISE ANALYSIS
                for ni = 1 : 2
                    % NEW FIGURE
                    figure(3 + ni)
                    tiledlayout(2,3, 'Padding', 'none', 'TileSpacing', 'compact');
                    % Case Structure to Deal With Real and Imaginary E-Fields
                    switch ni
                        case 1, field = ereal; nm = 'real';
                        case 2, field = eimag; nm = 'imag';
                    end

                    for j = 1 : 3 %Loop for each axis
                        % COMPUTE TABLE CONTAINING NOISE AND PLOT IN FIRST ROW
                        noise(:,:,j) = field(:,:,j) - medfilt2(field(:,:,j),'symmetric');
                        nexttile
                        imagesc(xcm,ycm,noise(:,:,j))
                        % Display Graphics Parameters
                        axis image
                        xlabel('X_0 [cm]')
                        ylabel('Y_0 [cm]')
                        caxis([-0.5,0.5])
                        set(gca,'Ydir','normal');
                        c = colorbar;
                        title(sprintf('%s %s',nm,xyz(j)))
                        c.Label.String = 'V/m';
                    end
                    colormap hsv

                    % Compute Noise Maximum for Graphics Scaling
                    noise_mx = 0.2*ceil(max(max(squeeze(std(noise))))/0.2);
                    % PLOT NOISE WITH UPDATED SCALING IN SECOND ROW
                    for j = 1 : 3
                        nexttile
                        plot(xcm,std(noise(:,:,j)),'x-','Linewidth',1.5)
                        xlabel('X_0 [cm]')
                        ylabel('Standard Deviation [V/m]')
                        ylim([0,noise_mx])
                    end 

                    % Graphics Parameters
                    set(gcf,'units','normalized','Position',[0.0,0.1,1.0,0.8])
                    set(findall(gcf,'-property','FontSize'),'FontSize',13)
                    drawnow;
                    % Export Graphics
                    if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json',sprintf('_noise_%s.jpg',nm)))); end
                end  % END OF FIGURE

                %Display Information To Console
                cprintf(colors{6},"done\n");
            else%Display Information To Console
                cprintf(colors{5},"skipped\n");
            end

            %% REMOVE MEDIAN FILTER
            %Display Information To Console
            fprintf("o) Apply median filter: ");

            if useMedianFilter
                for j = 1 : 3 % APPLY MEDIAN FILTER FOR EACH AXIS OF REAL AND IMAGINARY PART
                    ereal(:,:,j) = nanmedfilt2(ereal(:,:,j));
                    eimag(:,:,j) = nanmedfilt2(eimag(:,:,j));
                end
                %Display Information To Console
                cprintf(colors{6},"done\n");
            else
                %Display Information To Console
                cprintf(colors{5},"skipped\n");
            end

            %% DEFINE GRAPH MAXIMUM FOR SCALING PURPOSES
            %Display Information To Console
            fprintf("o) Get min/max values for scaling:\n");
            if isfield(caxis_mx,fi)
                zlim(1,:) = [-1,1] * caxis_mx.E;
                zlim(2,:) = [-1,1] * caxis_mx.I;
            else
                sorted = sort(abs(ereal(:)),'descend');
                zlim(1,:) = [-1,1] * mean(sorted(1:50));
                sorted = sort(abs(eimag(:)),'descend');
                zlim(2,:) = [-1,1] * mean(sorted(1:50));
            end
            %Display Information To Console
            fprintf("(real)");cprintf(colors{4},"%7.1f(min) %7.1f(max) [V/m]\n",zlim(1,1),zlim(1,2));
            fprintf("(imag)");cprintf(colors{4},"%7.1f(min) %7.1f(max) [V/m]\n",zlim(2,1),zlim(2,2));

            %% DISPLAY GRAPHICS
            ngr = 2;
            if displayModuleAndPhase
                emodu = abs(complex(ereal,eimag));

                % unwrapped phase (with PUMA algo)
                ePhasWrapped = angle(complex(ereal,eimag));

                % Direct
                ePhasA = wrapToPi(ePhasWrapped);
                phaLim = -pi+pi/4;
                ePhasA(ePhasA<phaLim) = ePhasA(ePhasA<phaLim)+2*pi;
                ephas = ePhasA;

                %                 dim = size(ephas);
                %                 oddx = mod(dim(1),2);
                %                 oddy = mod(dim(2),2);
                %                 for m = 1:3
                %                     pha = ephas(:,:,m);
                %                     if oddx, pha(dim(1)+1,:) = pha(dim(1),:);end
                %                     if oddy, pha(:,dim(2)+1) = pha(:,dim(2));end
                %                     pha_unw = puma_ho(pha,5,'verbose',false);
                %                     if oddx, pha_unw(dim(1)+1,:) = [];end
                %                     if oddy, pha_unw(:,dim(2)+1) = [];end
                %                     ephas(:,:,m) = pha_unw;
                %                 end
                ngr = 4;
                zlim(3,:) = sqrt(zlim(1,2).^2+zlim(2,2).^2) * [-1,1];
                zlim(4,:) = [-pi-pi/4,pi+pi/4];
            end
            if ~skipNonProjected
                fprintf("o) Display graphics");cprintf(colors{9}," (no projection)\n");
                for ni = 1 : ngr
                    figure(5 + ni)
                    %                     tiledlayout(1,3, 'Padding', 'none', 'TileSpacing', 'tight');
                    tiledlayout(3,1, 'Padding', 'none', 'TileSpacing', 'tight');
                    switch ni
                        case 1, field = ereal; nm = 'real';
                        case 2, field = eimag; nm = 'imag';
                        case 3, field = emodu; nm = 'modu';
                        case 4, field = ephas; nm = 'phas';
                    end
                    cprintf(colors{8}," %s\n",nm);
                    for j = 1 : nfi
                        nexttile
                        if rotateGraph
                            h = imagesc(ycm,xcm,flip(imrotate(field(:,:,j),90)));
                            xlabel('Y_0 [cm]')
                            if (j==1),ylabel('X_0 [cm]');end
                            set(gca,'Xdir','reverse')
                        else
                            h = imagesc(xcm,ycm,field(:,:,j));
                            xlabel('X_0 [cm]')
                            if (j==1),ylabel('Y_0 [cm]');end
                        end
                        set(gca,'Ydir','normal')
                        a = ancestor(h, 'axes');
                        a.XAxis.Exponent = 0;
                        a.YAxis.Exponent = 0;
                        axis image
                        colormap(jet)
                        c = colorbar;
                        cb = colorbar;
                        cb.Title.String = '[V/m]';
                        drawnow
                        title(sprintf('E_{%si} %s',xyz(j),nm))
                        caxis(zlim(ni,:))
                    end
                    if publi
                        %                         rect = [0.15,0.05+0.5*(1-mod(ni+1,2)),0.6,0.50];
                        rect = [0.15,0,0.3,1.0];
                    else
                        rect = [0.15,0.05+0.5*(1-mod(ni+1,2)),0.7,0.40];
                    end
                    set(gcf,'units','normalized','Position',rect)
                    set(findall(gcf,'-property','FontSize'),'FontSize',16)
                    %                 if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json',['-',nm,'_1.jpg']))); end
                end
            end

            % Assignation of data in new structure data
            data.E.xcm = xcm;
            data.E.ycm = ycm;
            data.E.im0 = ereal; % data.E.im0(y=n, x=p, :) = [Ex(x,y), Ey(x,y), Ez(x,y)]
            data.I.xcm = xcm;
            data.I.ycm = ycm;
            data.I.im0 = eimag; % data.E.im0(y=n, x=p, :) = [Ex(x,y), Ey(x,y), Ez(x,y)]

            %% Projection probe frame to test bench frame of reference
            fprintf("o) Projection from sensor frame to test bench frame\n");

            % Project components :
            % thx, thy and thz are the angle to pass from a straight cube
            % into the test bench frame to  a cube in ternary position so
            % Vec_ternary = (Rz(thz) * Ry(thy) * Rx(thx)) * Vec_bench
            % To do the reverse operation:
            % Vec_bench = (Rz(thz) * Ry(thy) * Rx(thx))^-1 * Vec_ternary
            % Vec_bench = (Rz(thz) * Ry(thy) * Rx(thx)) \ Vec_ternary
            % (other way to write it in matlab with backslash (M^-1 * V  = M \ V))



            bgdProj.E = (Rz(thz) * Ry(thy) * Rx(thx)) \ bgd.E;
            bgdProj.I = (Rz(thz) * Ry(thy) * Rx(thx)) \ bgd.I;
            fprintf("Field Excitation (projected):\n")
            fprintf("(real)");cprintf(colors{4},"%7.2f(Xp)%7.2f(Yp)%7.2f(Zp) [V/m]\n", bgdProj.E);
            fprintf("(imag)");cprintf(colors{4},"%7.2f(Xp)%7.2f(Yp)%7.2f(Zp) [V/m]\n", bgdProj.I);

            % Apply projection to real and imaginary parts
            img0 = ereal;
            dim = size(img0);
            data_1 = reshape(img0,dim(1)*dim(2),dim(3))';
            data_2 = (Rz(thz) * Ry(thy) * Rx(thx)) \ data_1;
            ereal2 = reshape(data_2',dim(1),dim(2),dim(3));

            img0 = eimag;
            dim = size(img0);
            data_1 = reshape(img0,dim(1)*dim(2),dim(3))';
            data_2 = (Rz(thz) * Ry(thy) * Rx(thx)) \ data_1;
            eimag2 = reshape(data_2',dim(1),dim(2),dim(3));

            % Use of quaternions
            Ereal_x = data.E.im0(:,:,1);
            Ereal_y = data.E.im0(:,:,2);
            Ereal_z = data.E.im0(:,:,3);
            Eimag_x = data.I.im0(:,:,1);
            Eimag_y = data.I.im0(:,:,2);
            Eimag_z = data.I.im0(:,:,3);
            %
            inverseRotation=true;
            ereal2 = rotationVectorFieldQuaternions(Ereal_x, Ereal_y, Ereal_z, thx, thy, thz, inverseRotation ); %Use of the function to rotate a Vector Field with quaternions, see the associated file in Function folder
            eimag2 = rotationVectorFieldQuaternions(Eimag_x, Eimag_y, Eimag_z, thx, thy, thz, inverseRotation); %Use of the function to rotate a Vector Field with quaternions, see the associated file in Function folder

            if displayModuleAndPhase
                emodu2 = abs(complex(ereal2,eimag2));

                ePhasWrapped = angle(complex(ereal2,eimag2));
                ePhasA = wrapToPi(ePhasWrapped);
                ePhasA(ePhasA<phaLim) = ePhasA(ePhasA<phaLim)+2*pi;

                testUnwrapping = false;
                if testUnwrapping
                    ePhasB = zeros(size(ePhasWrapped));
                    for j = 1:3
                        ePhasB(:,:,j) = unwrap_phase(ePhasWrapped(:,:,j));
                    end

                    ePhasC = zeros(size(ePhasWrapped));
                    for j = 1:3
                        ePhasC(:,:,j) = phase_unwrap(ePhasWrapped(:,:,j));
                    end
                    % Display
                    figure(101)
                    imagesc([ePhasA(:,:,1),ePhasB(:,:,1),ePhasC(:,:,1); ...
                        ePhasA(:,:,2),ePhasB(:,:,2),ePhasC(:,:,2); ...
                        ePhasA(:,:,3),ePhasB(:,:,3),ePhasC(:,:,3);])
                end
                ephas2 = ePhasA;
                %                 ephas2 = angle(complex(ereal2,eimag2));
                %                 dim = size(ephas2);
                %                 oddx = mod(dim(1),2);
                %                 oddy = mod(dim(2),2);
                %                 for m = 1:3
                %                     pha = ephas2(:,:,m);
                %                     if oddx, pha(dim(1)+1,:) = pha(dim(1),:);end
                %                     if oddy, pha(:,dim(2)+1) = pha(:,dim(2));end
                %                     pha_unw = puma_ho(pha,5,'verbose',false);
                %                     if oddx, pha_unw(dim(1)+1,:) = [];end
                %                     if oddy, pha_unw(:,dim(2)+1) = [];end
                %                     ephas2(:,:,m) = pha_unw;
                %                 end

            end

            %% DISPLAY GRAPHICS WITH PROJECTION APPLIED
            fprintf("o) Display graphics");cprintf(colors{9}," (with projection)\n");
            for ni = 1 : ngr
                % NEW FIGURES
                figure(9 + ni)
                tiledlayout(1,3, 'Padding', 'none', 'TileSpacing', 'compact');
                switch ni
                    case 1, field = ereal2; nm = 'real';
                    case 2, field = eimag2; nm = 'imag';
                    case 3, field = emodu2; nm = 'modu';
                    case 4, field = ephas2; nm = 'phas';
                end
                cprintf(colors{8}," %s\n",nm);
                for j = 1 : nfi
                    nexttile
                    if rotateGraph
                        h = imagesc(ycm,xcm,flip(imrotate(field(:,:,j),90)));
                        if showContour
                            hold on
                            contour(ycm,xcm,flip(imrotate(field(:,:,j),90)),max(zlim(:,2))*(-1:0.125:1),'k')
                            hold off
                        end
                        xlabel('Y_0 [cm]')
                        if (j==1),ylabel('X_0 [cm]');end
                        set(gca,'Xdir','reverse')
                    else
                        h = imagesc(xcm,ycm,field(:,:,j));
                        if showContour
                            hold on
                            contour(xcm,ycm,field(:,:,j),max(zlim(:,2))*(-1:0.125:1),'k')
                            hold off
                        end
                        xlabel('X_0 [cm]')
                        if (j==1),ylabel('Y_0 [cm]');end
                    end
                    % Graphics Parameters
                    set(gca,'Ydir','normal')
                    a = ancestor(h, 'axes');
                    a.XAxis.Exponent = 0;
                    a.YAxis.Exponent = 0;
                    axis image
                    colormap(jet)
                    c = colorbar;
                    cb = colorbar;
                    cb.Title.String = '[V/m]';
                    drawnow
                    title(sprintf('E_{%s} %s',xyz(j),nm))
                    % COMPUTE ZOFFSET IF NEEDED
                    if zoffset
                        offsetBord = mean([mean(field(1,:,j)),mean(field(end,:,j)),mean(field(:,1,j)),mean(field(:,end,j))]);
                        zoff = offsetBord;
                        title(sprintf('E_{%s} %s, E_{offset} = %3.1fV/m',xyz(j),nm,offsetBord))
                    else
                        zoff = 0;
                    end
                    caxis(zoff + zlim(ni,:))
                    if publi
                        newmx = ceil(max(max(abs(field(:,:,j)))));
                        caxis(zoff + [-newmx,newmx]);
                    end
                end

                if publi
                    rect = [0.15,0.05+0.5*(1-mod(ni+1,2)),0.6,0.50];
                else
                    rect = [0.15,0.05+0.5*(1-mod(ni+1,2)),0.7,0.40];
                end
                set(gcf,'units','normalized','Position',rect)
                set(findall(gcf,'-property','FontSize'),'FontSize',16)
                if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json',['-',nm,'_2.jpg']))); end
            end % END OF FIGURES

            % ASSIGNATION OF DATA
            data.E.im = ereal2;
            data.I.im = eimag2;

            %% Phase Analysis
            clear img1;
            fprintf('o) Phase analysis ');
            if ~skipPhaseAnalysis
                figure(13)
                tiledlayout(3,4, 'Padding', 'none', 'TileSpacing', 'compact');
                for j = 1:3
                    vreal = data.E.im0(:,:,j);
                    vimag = data.I.im0(:,:,j);
                    ratio = vimag./vreal;

                    threshold_percentage = 0.25;
                    real_sort = sort(abs(vreal(:)),'descend');
                    real_mx = mean(real_sort(1:100));
                    mask = ones(size(vreal));
                    mask(abs(vreal) < threshold_percentage * real_mx) = NaN;

                    % Define graph maximum
                    if isfield(caxis_mx,'E')
                        mx = caxis_mx.(fi);
                    else
                        mx =real_mx;
                    end
                    zlim = [-mx,mx];

                    nexttile
                    imagesc(xcm,ycm,vreal)
                    axis image
                    xlabel('X_0 [cm]'); ylabel('Y_0 [cm]')
                    set(gca,'Ydir','normal');
                    c = colorbar;
                    c.Label.String = ['Ereal_',xyz(j)];
                    caxis(zlim)

                    nexttile
                    imagesc(xcm,ycm,vimag)
                    axis image
                    xlabel('X_0 [cm]'); ylabel('Y_0 [cm]')
                    set(gca,'Ydir','normal');
                    c = colorbar;
                    c.Label.String = ['Eimag_',xyz(j)];
                    caxis(zlim)

                    mag = abs(complex(vreal,vimag));
                    pha = angle(complex(vreal,vimag));

                    tmp = mask.*atan(vimag./vreal);
                    tmp(isnan(tmp)) = [];
                    depha(j) = -mean(tmp);

                    vreal2 = real(mag.*exp(1i*(pha+depha(j))));
                    vimag2 = imag(mag.*exp(1i*(pha+depha(j))));
                    img1(:,:,j) = vreal2;

                    mag_sorted = sort(mag(:),'descend');
                    mag_mx = mean(mag_sorted(1:10));

                    nexttile
                    imagesc(xcm,ycm,mag)
                    axis image
                    xlabel('X_0 [cm]'); ylabel('Y_0 [cm]')
                    title(sprintf('Max amplitude: %3.1f',mag_mx))
                    set(gca,'Ydir','normal');
                    c = colorbar;
                    c.Label.String = ['Amplitude R_',xyz(j)];

                    nexttile
                    imagesc(xcm,ycm,mask.*atand(vimag./vreal))
                    caxis([-90,90])
                    axis image
                    xlabel('X_0 [cm]'); ylabel('Y_0 [cm]')
                    title(sprintf('Average phase: %3.1f°',180/pi*depha(j)))
                    set(gca,'Ydir','normal');
                    c = colorbar;
                    c.Label.String = ['Phase shift \phi_',xyz(j),' [rad]'];
                end
                colormap jet
                set(gcf,'units','normalized','Position',[0.10,0.05,0.8,0.95])
                set(findall(gcf,'-property','FontSize'),'FontSize',12)
                if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json','_phaseanalysis.jpg'))); end

                % Project the X, Y and Z components measured with the probe in the XYZ bench referential
                thx = theta(1) + corr(1);
                thy = theta(2) + corr(2);
                thz = theta(3) + corr(3);

                dim = size(img1);
                data_1 = reshape(img1,dim(1)*dim(2),dim(3))';
                data_2 = (Rz(thz) * Ry(thy) * Rx(thx)) \ data_1;
                data_3 = reshape(data_2',dim(1),dim(2),dim(3));

                mx =  max(max(max(abs((data_3)))));
                zlim = [-mx,mx];

                figure(14)
                tiledlayout(1,3, 'Padding', 'none', 'TileSpacing', 'compact');
                for j = 1 : 3
                    nexttile
                    imagesc(xcm,ycm,data_3(:,:,j))
                    axis image
                    xlabel('X_0 [cm]')
                    ylabel('Y_0 [cm]')
                    set(gca,'Ydir','normal');
                    caxis(zlim)
                    c = colorbar;
                    c.Label.String = 'V/m';
                    title(sprintf('E_{%s} %s',xyz(j),'real'))
                end
                colormap jet
                set(gca,'Ydir','normal')
                set(gcf,'units','normalized','Position',[0.15,0.55,0.7,0.40])
                set(findall(gcf,'-property','FontSize'),'FontSize',13)
                if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json',['-','E_3.jpg']))); end
                cprintf(colors{6},"done\n");
            else
                cprintf(colors{5},"skipped\n");
            end


            %% POST-PROCESSING PART FOR MAGL SENSOR
        elseif strcmp(fi,'M') || strcmp(fi,'A') || strcmp(fi,'G')   || strcmp(fi,'L')
            cprintf(colors{7},'\n-> Field: %c',fi);cprintf('white',"\n");
            data_fi = dataB.(fi);
            nfi = length(infoM.(fi));
            ycm = yBcm;

            clear img; clear nm;
            img = zeros(size(data_fi));
            for j = 1 : nfi
                suff = [];
                switch fi
                    case 'M'
                        if removeBackground
                            img(:,:,j) = 1e6 * (data_fi(:,:,j)-dataB_BG.M(:,:,j));
                            suff = '-Bgd';
                            tit = 'Magnetic Field, Background removed';
                        else
                            img(:,:,j) = 1e6 * data_fi(:,:,j);
                            tit = 'Magnetic Field';
                        end
                        nm{j} = ['B_',xyz(j),'[µT]'];
                    case 'A'
                        img(:,:,j) = data_fi(:,:,j);
                        nm{j} = ['Acc_',xyz(j),'[g]'];
                        tit = 'Accelerometer';
                    case 'G'
                        img(:,:,j) = data_fi(:,:,j);
                        nm{j} = ['Gyro_',xyz(j),'[dps]'];
                        tit = 'Gyroscope';
                    case 'L'
                        img(:,:,j) = data_fi(:,:,j);
                        nm{j} = ['Lidar',xyz(j),'[mm]'];
                        tit = 'Lidar';
                end
            end

            fprintf("o) Apply median filter: ");
            if useMedianFilter
                for j = 1 : 3
                    img(:,:,j) = nanmedfilt2(img(:,:,j));
                end
                cprintf(colors{6},"done\n");
            else
                cprintf(colors{5},"skipped\n");
            end

            %             % Define graph maximum
            %             if isfield(caxis_mx,fi)
            %                 mx = caxis_mx.(fi);
            %             else
            %                 sorted = sort(abs(img(:)),'descend');
            %                 mx = mean(sorted(1:50));
            %             end
            %             zlim = [-mx,mx];

            % Display graphics
            fprintf('o) Display graphics \n')
            figure(10 + i)
            tiledlayout(1,nfi, 'Padding', 'none', 'TileSpacing', 'compact');
            sgn = bparam{1}; % change sign or not
            img = sgn * img;
            for j = 1 : nfi
                nexttile
                imgj = img(:,:,j);
                h = imagesc(xcm,ycm,imgj);
                set(gcf,'units','normalized','Position',[0.0,0.2,1.0,0.6])
                set(gca,'Ydir','normal')
                a = ancestor(h, 'axes');
                xlabel('X_0 [cm]')
                ylabel('Y_0 [cm]')
                a.XAxis.Exponent = 0;

                a.YAxis.Exponent = 0;
                axis image
                colormap(jet)
                c = colorbar;
                drawnow
                title(nm{j})
                c.Label.String = 'µT';
                % Define graph maximum
                if isfield(caxis_mx,fi)
                    mx = caxis_mx.(fi);
                    zlim = [-mx,mx];
                else
                    sorted = sort(imgj(:),'descend');
                    mx = mean(sorted(1:50));
                    sorted = sort(imgj(:),'ascend');
                    mn = mean(sorted(1:50));
                    if strcmp(bparam{2}(j),'S')
                        mx = max(mx,-mn);
                        zlim = [-mx,mx];
                    else
                        zlim = [mn,mx];
                    end
                end

                caxis(zlim)
                if strcmp(fi,'L')
                    colormap(flip(jet))
                    set(gcf,'units','normalized','Position',[0.3,0.2,0.4,0.6])
                    caxis(zlim.*[0,1])
                end
            end
            set(findall(gcf,'-property','FontSize'),'FontSize',13)
            if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json',['-',fi,suff,'_1.jpg']))); end

            data.(fi).xcm = xcm;
            data.(fi).ycm = ycm;
            data.(fi).im = img;

            %% LIDAR further processing
            if isfield(data,'L')
                % 2D interpolation to get same step in X and Y
                stp = min([mean(diff(xcm)),mean(diff(ycm))]);
                x2 = xcm(1):stp:xcm(end);
                y2 = ycm(1):stp:ycm(end);
                [xx,yy] = meshgrid(xcm,ycm);
                [xx2,yy2] = meshgrid(x2,y2);
                im = interp2(xx,yy,img,xx2,yy2);

                % filter images
                im = medfilt2(im);
                im = imfilter(im,fspecial('gaussian',4,4));

                % remove last  values
                border_val = mean(img(1,:));
                border = 6;
                im(1:border,:) = border_val;
                im(:,1:border) = border_val;
                im(end-border:end,:) = border_val;
                im(:,end-border:end) = border_val;

                % translate correction
                im = imtranslate(im,lidar_trans_cm/stp,'FillValues',border_val);

                % Get max from highest values (use lidar_range if values assigned)
                if ~isempty(lidar_range)
                    zlim = lidar_range;
                else
                    im_sort = sort(im(:),'ascend');
                    mn = mean(im_sort(1:100));
                    sorted = sort(abs(im(:)),'ascend');
                    sorted(isnan(sorted)) = [];
                    mn = mean(sorted(1:10));
                    sorted = sort(abs(im(:)),'descend');
                    sorted(isnan(sorted)) = [];
                    mx = mean(sorted(1:10));
                    zlim = [mn,mx];
                end

                % Get profiles data if any
                rect = [0.3,0.2,0.4,0.6]; npx = 0; npy = 0;
                smooth_hw = 30;
                if ~isempty(lidar_profile)
                    xpf = lidar_profile(contains(lidar_profile,'x'));
                    ypf = lidar_profile(contains(lidar_profile,'y'));
                    npx = length(xpf); npy = length(ypf);
                    nix = length(x2); niy = length(y2);
                    pf_x = zeros(niy,npx); pos_x = zeros(npx,1);
                    pf_y = zeros(nix,npy); pos_y = zeros(npx,1);
                    for k = 1:npx
                        pf = str2double(strrep(xpf{k},'x',''));
                        [~,loc] = min(abs(x2 - pf));
                        pf_x(:,k) = mean(im(:,loc-smooth_hw+1:loc+smooth_hw),2);
                        pos_x(k) = x2(loc);
                    end
                    for k = 1:npy
                        pf = str2double(strrep(ypf{k},'y',''));
                        [~,loc] = min(abs(y2 - pf));
                        pf_y(:,k) = mean(im(loc-smooth_hw+1:loc+smooth_hw,:),1)';
                        pos_y(k) = y2(loc);
                    end
                    if (npx>0), rect(1) = 0.2; rect(3) = 0.6; end
                    if (npy>0), rect(2) = 0.05; rect(4) = 0.9; end
                end

                figure(10)
                tiledlayout(1+(npy>0),1+(npx>0), 'Padding', 'none', 'TileSpacing', 'compact');
                set(gcf,'units','normalized','Position',rect)
                nexttile
                h = imagesc(x2,y2,im);

                % DETECT SPHERE USING LIDAR
                if detectSphere
                    hmx = mn + 30;
                    bn = imopen((im > hmx),strel('disk',10));
                    [centers,radii] = imfindcircles(bn,[5 45],'ObjectPolarity','dark','Sensitivity',0.7,'Method','twostage');

                    n_cir = length(radii);
                    for k = 1 : n_cir
                        viscircles([x2(round(centers(k,1))),y2(round(centers(k,2)))],stp*mean(radii),'Color','k');
                    end
                    if n_cir > 1
                        np = nchoosek(1:n_cir,2);
                        for k = 1 : size(np,1)
                            hold on
                            p1 = [x2(round(centers(np(k,1),1))),x2(round(centers(np(k,2),1)))];
                            p2 = [y2(round(centers(np(k,1),2))),y2(round(centers(np(k,2),2)))];
                            dist = sqrt(diff(p1)^2+diff(p2)^2);
                            plot(p1,p2,'kx-','Linewidth',1.5)
                            text(mean(p1)+0.2,mean(p2)+0.1*diff(p2),sprintf('%3.2f',dist),'HorizontalAlignment', 'center','Fontsize',10)
                        end
                        hold off
                    end
                end
                set(gca,'Ydir','normal')
                a = ancestor(h, 'axes');
                xlabel('X_0 [cm]')
                ylabel('Y_0 [cm]')
                a.XAxis.Exponent = 0;
                a.YAxis.Exponent = 0;
                axis image
                colormap(jet)
                c = colorbar;
                drawnow
                title('LIDAR [mm]')
                colormap(flip(jet))
                caxis(zlim)
                set(findall(gcf,'-property','FontSize'),'FontSize',16)

                if ~isempty(lidar_profile)
                    % Plot profiles on the graph
                    hold on
                    cmapx = summer(npx+1); cmapy = copper(npy+1);
                    for k = 1:npx, plot([pos_x(k),pos_x(k)],[min(y2),max(y2)],'Color',cmapx(k,:),'Linewidth',2); end
                    for k = 1:npy, plot([min(x2),max(x2)],[pos_y(k),pos_y(k)],'Color',cmapy(k,:),'Linewidth',2); end
                    hold off

                    if npx>0
                        nexttile
                        for k = 1 : npx
                            plot(pf_x(:,k),y2','Color',cmapx(k,:),'Linewidth',2);
                            hold on
                            xlim(zlim)
                            ylim([min(y2),max(y2)])
                            axis square
                        end
                        xlabel('Zs[cm]')
                        ylabel('Y_0 [cm]')
                        legend(xpf)
                        hold off
                    end
                    if npy>0
                        nexttile
                        for k = 1 : npy
                            plot(x2',pf_y(:,k),'Color',cmapy(k,:),'Linewidth',2);
                            hold on
                            xlim([min(x2),max(x2)])
                            ylim(zlim)
                            axis square
                        end
                        xlabel('X_0[cm]')
                        ylabel('Zs[cm]')
                        legend(ypf)
                        hold off
                    end
                end

                % title(sprintf('Z Lidar-Sphere = %3.1f mm', mn))
                if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json','_LIDAR_proc.jpg'))); end
            end
        end
    end

    %%  E-FIELD : UPDATING JSON FILE WITH PROCESSING PARAMETERS AND SAVING DATA TO CSV FILE
    %Display Information To Console
    fprintf('\n-> Updating JSON file with processing parameters\n');
    fprintf('   and saving data to CSV file\n');

    if exist('dataE','var')
        xE = xcm;
        nxE = length(xE);
        nyE = length(yEcm);
        ntot = nxE*nyE;
        [xxE,yyE] = meshgrid(xE,yEcm);
        dataOut       = zeros(ntot,16);
        dataOut(:,1)  = reshape(xxE,ntot,1) * 10 / (incToMm);
        dataOut(:,2)  = reshape(yyE,ntot,1) * 10 / (incToMm);
        dataOut(:,3)  = reshape(xxE,ntot,1);
        dataOut(:,4)  = reshape(yyE,ntot,1);
        dataOut(:,5)  = reshape(dataE.E(:,:,1),ntot,1);
        dataOut(:,6)  = reshape(dataE.E(:,:,2),ntot,1);
        dataOut(:,7)  = reshape(dataE.E(:,:,3),ntot,1);
        dataOut(:,8)  = reshape(dataE.I(:,:,1),ntot,1);
        dataOut(:,9)  = reshape(dataE.I(:,:,2),ntot,1);
        dataOut(:,10) = reshape(dataE.I(:,:,3),ntot,1);
        dataOut(:,11) = reshape(data.E.im(:,:,1),ntot,1);
        dataOut(:,12) = reshape(data.E.im(:,:,2),ntot,1);
        dataOut(:,13) = reshape(data.E.im(:,:,3),ntot,1);
        dataOut(:,14) = reshape(data.I.im(:,:,1),ntot,1);
        dataOut(:,15) = reshape(data.I.im(:,:,2),ntot,1);
        dataOut(:,16) = reshape(data.I.im(:,:,3),ntot,1);
        pathOut = strrep(pathJson,'.json','_proc.csv');
        dlmwrite(pathOut,dataOut,',');

        dat = datestr(now,'yyyy-mm-dd HH:MM:SS');
        J.processing.date            = dat;
        J.processing.imageSize       = [nyE,nxE];
        J.processing.incToMm         = incToMm;
        J.processing.VToVpM          = VtoVpmField;
        J.processing.offsets.E       = offset.E;
        J.processing.offsets.I       = offset.I;
        J.processing.phase           = phase;
        J.processing.bgd.E           = bgd.E;
        J.processing.bgd.I           = bgd.I;
        J.processing.medianFilter    = useMedianFilter;
        J.processing.delayMs         = delay_ms;
        J.processing.background      = removeBackground;
        J.processing.corrAnglProjDeg = corr;
        opt.FileName = pathJson;
        savejson([],J,opt);

        %% SAVING DATA TO MAT FILE
        pathMat = fullfile(pathSave,strrep(jsonname,'.json','.mat'));
        save(pathMat,'data')
        %Display Information To Console
        fprintf('\n-> Save to MAT file:\n');cprintf(colors{2},"    %s",fileparts(pathMat));cprintf('white',"\n");

        %% B-FIELD : UPDATING JSON AND SAVING DATA
    elseif exist('dataB','var')
        xB = xcm;
        nxB = length(xB);
        nyB = length(yBcm);
        ntot = nxB*nyB;
        [xxB,yyB] = meshgrid(xB,yBcm);
        dataOut       = zeros(ntot,16);
        dataOut(:,1)  = reshape(xxB,ntot,1) * 10 / (incToMm);
        dataOut(:,2)  = reshape(yyB,ntot,1) * 10 / (incToMm);
        dataOut(:,3)  = reshape(xxB,ntot,1);
        dataOut(:,4)  = reshape(yyB,ntot,1);
        dataOut(:,5)  = reshape(data.M.im(:,:,1),ntot,1);
        dataOut(:,6)  = reshape(data.M.im(:,:,2),ntot,1);
        dataOut(:,7)  = reshape(data.M.im(:,:,3),ntot,1);
        pathOut = strrep(pathJson,'.json','_proc.csv');
        dlmwrite(pathOut,dataOut,',');

        dat = datestr(now,'yyyy-mm-dd HH:MM:SS');
        J.processing.date            = dat;
        J.processing.imageSize       = [nyB,nxB];
        J.processing.incToMm         = incToMm;
        J.processing.background      = removeBackground;
        opt.FileName = pathJson;
        savejson([],J,opt);

        %% B-FIELD : SAVING TO MAT FILE
        pathMat = fullfile(pathSave,strrep(jsonname,'.json','.mat'));
        save(pathMat,'data')
        fprintf('\n-> Save to MAT file:\n');cprintf(colors{2},"    %s",pathMat );cprintf('white',"\n");
    end
end

%% Shape reconstruction
if shapeRecognition
    % Ferme toutes les figures ouvertes
    close all

    % Initialise les données d'entrée
    E0 = eimag2;
    xcm0 = xcm - mean(xcm);
    ycm0 = ycm - mean(ycm);

    % Paramètres de l'image
    dim = 1024;             % image full-size number of pixels /0-paddingEx
    xm = 30;                % image full size dimension in cm /0-padding
    border = 20;            % number of pixels on image border for background plane fit
    nsr = 100;               % noise-to-signal-ratio
    Edipole = [0,1,0];      % dipole orientation [x,y,z]
    z0 = 2;                 % distance plane to dipole
    thresh = 0.01;          % thresuhold final cleaning

    % 1) 0-PADDING + BACKGROUND REMOVAL (PLANE FIT) ON DATA MEASUREMENT
    xcm1 = linspace(-xm,xm,dim);
    ycm1 = linspace(-xm,xm,dim);
    step = mean(diff(xcm1));
    [xx0,yy0] = meshgrid(xcm0,ycm0);
    [xx1,yy1] = meshgrid(xcm1,ycm1);

    % Crée un masque pour les données valides après l'interpolation
    m = ones(size(E0(:,:,1)));
    mi = ~isnan(interp2(xx0,yy0,m,xx1,yy1));

    E1 = zeros([size(xx1),3]);
    for i = 1 : 3
        Ea = E0(:,:,i);
        Ei = interp2(xx0,yy0,Ea,xx1,yy1);

        % Plane fit from image border
        xf = [xx0(1:border,:),xx0(end-border+1:end,:),xx0(:,1:border)',xx0(:,end-border+1:end)'];
        yf = [yy0(1:border,:),yy0(end-border+1:end,:),yy0(:,1:border)',yy0(:,end-border+1:end)'];
        zf = [Ea(1:border,:),Ea(end-border+1:end,:),Ea(:,1:border)',Ea(:,end-border+1:end)'];
        N = length(xf(:));
        O = ones(N,1);
        C = [xf(:) yf(:) O]\zf(:);
        plane = xx1 * C(1) + yy1*C(2) + C(3);

        Ei(mi) = Ei(mi) - plane(mi);
        Ei(~mi) = 0;

        E1(:,:,i) = Ei;
    end

    % Affiche les images après ajusement de l'arrière-plan
    figure(101)
    tiledlayout(1,3,'Padding', 'none', 'TileSpacing', 'compact');
    for i = 1 : 3
        nexttile;
        imagesc(xcm1,ycm1,E1(:,:,i)/max(max(abs(E1(:,:,i)))));
        axis image;
        caxis([-1,1])
        xlabel('X [cm]')
        ylabel('Y [cm]')
        set(gca,'ydir','normal')
    end
    colormap jet
    set(gcf,'units','normalized','Position',[0.2,0.3,0.6,0.4])
    % if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json','_deconv1.jpg')));end

    % 2)GENERATE DIPOLE ELECTRIC FIELD MAPS
    z = z0-step:step:z0+step;
    [xx,yy,zz] = meshgrid(xcm1,ycm1,z);
    E0x = repmat(Edipole(1),size(xx)); E0y = repmat(Edipole(2),size(xx)); E0z = repmat(Edipole(3),size(xx));
    E0r = cat(4,E0x,E0y,E0z);
    rr = cat(4,xx,yy,zz);
    rra = sqrt(sum(rr.^2,4));
    dV = sum(rr .* E0r,4) ./ rra.^3;

    % Calcul les gradients
    [Ex,Ey,Ez] = imgradientxyz(dV,'central');

    Ed = zeros([size(xx1),3]);
    Ed(:,:,1) = Ex(:,:,2);
    Ed(:,:,2) = Ey(:,:,2);
    Ed(:,:,3) = Ez(:,:,2);

    %Affichage des cartes de champ électrique du dipôle, normalisé
    figure(102)
    tiledlayout(1,3,'Padding', 'none', 'TileSpacing', 'compact');
    for i = 1 : 3
        nexttile;
        imagesc(xcm1,ycm1,Ed(:,:,i)/max(max(abs(Ed(:,:,i)))));
        axis image;
        caxis([-1,1])
        xlabel('X [cm]')
        ylabel('Y [cm]')
        set(gca,'ydir','normal')
    end
    colormap jet
    set(gcf,'units','normalized','Position',[0.0,0.5,0.6,0.4])
    % if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json','_deconv2.jpg')));end

    % 3) APPLY WIENER DECONVOLUTION
    figure(103)
    tiledlayout(1,3,'Padding', 'none', 'TileSpacing', 'compact');
    clear E2
    for i = 1 : 3
        E2(:,:,i) = deconvwnr(E1(:,:,i),Ed(:,:,i),nsr); %Wiener Deconvolution
        nexttile;
        imagesc(xcm1,ycm1,E2(:,:,i)/max(max(abs(E2(:,:,i)))));
        axis image;
        caxis([-1,1])
        xlabel('X [cm]')
        ylabel('Y [cm]')
        set(gca,'ydir','normal')
    end
    colormap jet
    set(gcf,'units','normalized','Position',[0.0,0.1,0.6,0.4])
    % if exportGraphicOn, exportgraphics(gcf,fullfile(pathSave,strrep(jsonname,'.json','_deconv3.jpg')));end


    % 4) PROCESS DECONVOLVED IMAGES


    % Ed = E2(:,:,1)/max(max(abs(E2(:,:,1))))+E2(:,:,3)/max(max(abs(E2(:,:,3))));
    % Ea = abs(E2(:,:,2));
    Et = E2;
    for i = 1:3
        mn = min(min(Et(:,:,i)));
        mx = max(max(Et(:,:,i)));
        if abs(mn) > abs(mx)
            Et(:,:,i) = -Et(:,:,i);
        end
    end


    Et(Et<0.0) = 0;

    Ea = abs(Et(:,:,1).*Et(:,:,2).*Et(:,:,3));
    %     Ea = sqrt(sum(Et.^2,3));
    Ea(Ea<thresh*max(Ea(:)))=0;
    Ed = nthroot(Ea,3);
    Eds = imgradient(Ed,'central');
    Edn = Ed/max(max(abs(Ed)));
    Edsn = Eds/max(max(abs(Eds)));

    figure(104)
    tiledlayout(1,2,'Padding', 'none', 'TileSpacing', 'compact');
    nexttile;
    imagesc(xcm1,ycm1,Edn);
    axis image;
    caxis([-1,1])
    xlabel('X [cm]')
    ylabel('Y [cm]')
            ylabel('Y [cm]')
        set(gca,'ydir','normal')
end