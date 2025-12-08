MOC :
Source : [[Luis Saluden]]
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Simulation :
Tags : #NoteAtomique
Date : 2025-06-10
***

PORT COM 5
BAUDRATE : 256000


% Specify how data are stored in .csv data file (minus sign to reverse axis)
% MAGL sensor
infoM.M = [-4,-3,5];    % Magnetic field [X, Y, Z] --> Stored at rows 3,4,5
infoM.A = [-7,-6,8];    % Accelerometer  [X, Y, Z]
infoM.G = [-10,-9,11];  % Gyrometer      [X, Y, Z]
infoM.L = 12;           % LIDAR          H
infoM.t = 13;           % Time           t
infoM.s = 14;           % Scanning state b