function E_rotated_quat = rotationVectorFieldQuaternions(E_x, E_y, E_z, theta_x, theta_y, theta_z, inverse)
% Author : Luis Saluden
% Date : 2024-10-04
% rotate_vector_field Rotates a 3D vector field using quaternion rotation
% Inputs:
%   E_x      : Composante x du champ de vecteurs (matrix)
%   E_y      : Composante y du champ de vecteurs (matrix)
%   E_z      : Composante z du champ de vecteurs (matrix)
%   theta_x  : Angle de rotation autour de l'axe x (en degrés)
%   theta_y  : Angle de rotation autour de l'axe y (en degrés)
%   theta_z  : Angle de rotation autour de l'axe z (en degrés)
%   inverse  : Boolean flag, if true applies inverse rotation
% Output:
%   E_rotated_quat : Champ de vecteurs tourné (3D matrix)

    % Définir les angles de rotation en radians
    theta_x = deg2rad(theta_x);
    theta_y = deg2rad(theta_y);
    theta_z = deg2rad(theta_z);

    % Créer les quaternions pour chaque rotation
    qx = [cos(theta_x/2), -sin(theta_x/2), 0, 0];
    qy = [cos(theta_y/2), 0, -sin(theta_y/2), 0];
    qz = [cos(theta_z/2), 0, 0, -sin(theta_z/2)];

    qx = qx / norm(qx);
    qy = qy / norm(qy);x
    qz = qz / norm(qz);

    % Combiner les quaternions (ordre: x, y, z)
    q_temp = quatmultiply(qx, qy);
    q = quatmultiply(q_temp, qz);

    q = q/norm(q);
    % Check if inverse rotation is requested
    if inverse
        % Inverse quaternion is simply its conjugate: [q0, -q1, -q2, -q3]
        q = [q(1), -q(2), -q(3), -q(4)];
    end

    % Créer un tableau de vecteurs E pour chaque point
    [ny, nx] = size(E_x);
    E_vectors = cat(3, E_x, E_y, E_z); % Inclure E_z

    % Préparer le tableau contenant la rotation du champ de vecteurs par quaternion
    E_rotated_quat = zeros(size(E_vectors));

    % Effectuer la rotation du champ de vecteurs
    for i = 1:nx
        for j = 1:ny
            v = squeeze(E_vectors(j, i, :));
            E_rotated_quat(j, i, :) = quatrotate(q, v');
        end
    end
end
