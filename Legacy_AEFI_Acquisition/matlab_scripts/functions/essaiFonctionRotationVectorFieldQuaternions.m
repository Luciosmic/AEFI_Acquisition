% Example Script
close all;
clear all;

% Définir les points de la grille dans le plan (x, y)
x = linspace(-2, 2, 5);
y = linspace(-2, 2, 7);
[X, Y] = meshgrid(x, y);

% Définir le champ de vecteurs E(x, y)
E_x = Y;      % Composante x du champ de vecteurs
E_y = -X;     % Composante y du champ de vecteurs
E_z = X + Y;  % Composante z du champ de vecteurs (exemple non nul)

% Définir les angles de rotation (en degrés)
theta_x = 90;  % Pas de rotation autour de x
theta_y = 45;  % Rotation de 0 degrés autour de y
theta_z = 0; % Rotation de 90 degrés autour de z

% Appeler la fonction pour obtenir le champ de vecteurs tourné
E_rotated_quat = rotationVectorFieldQuaternions(E_x, E_y, E_z, theta_x, theta_y, theta_z, false); %false signifie que la rotation est dans le sens direct, on peut inverser la rotation en changeant par true

% Visualiser le champ de vecteurs original et tourné
figure;

% Champ de vecteurs original
subplot(1, 2, 1);
quiver3(X, Y, zeros(size(E_x)), E_x, E_y, E_z, 'b');
title('Champ de vecteurs original');
xlabel('x');
ylabel('y');
zlabel('z');
axis equal;
grid on;

% Champ de vecteurs tourné par quaternion
subplot(1, 2, 2);
quiver3(X, Y, zeros(size(E_x)), squeeze(E_rotated_quat(:, :, 1)), squeeze(E_rotated_quat(:, :, 2)), squeeze(E_rotated_quat(:, :, 3)), 'r');
title('Champ de vecteurs tourné (Quaternion)');
xlabel('x');
ylabel('y');
zlabel('z');
axis equal;
grid on;

% Ajuster la figure
set(gcf, 'Position', [100, 100, 1200, 500]);
