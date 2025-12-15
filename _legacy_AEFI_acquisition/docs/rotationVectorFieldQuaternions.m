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
    qy = qy / norm(qy);
    qz = qz / norm(qz);

    % Combiner les quaternions (ordre: x, y, z)
    q_temp = customQuatMultiply(qx, qy);
    q = customQuatMultiply(q_temp, qz);

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
            E_rotated_quat(j, i, :) = customQuatRotate(q, v');
        end
    end
end


function q_result = customQuatMultiply(q1, q2)
% CUSTOMQUATMULTIPLY Multiplies two quaternions q1 and q2.
% Inputs:
%   q1 : First quaternion (1x4 vector) [q0, q1, q2, q3]
%   q2 : Second quaternion (1x4 vector) [q0, q1, q2, q3]
% Output:
%   q_result : Resultant quaternion from the multiplication (1x4 vector)

    % Extract individual components
    w1 = q1(1); x1 = q1(2); y1 = q1(3); z1 = q1(4);
    w2 = q2(1); x2 = q2(2); y2 = q2(3); z2 = q2(4);
    
    % Calculate the product
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2;
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2;
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2;
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2;

    % Combine results into a quaternion
    q_result = [w, x, y, z];
end

function v_rotated = customQuatRotate(q, v)
% CUSTOMQUATROTATE Rotates a vector by a quaternion
% Inputs:
%   q : Quaternion representing the rotation (1x4 vector) [q0, q1, q2, q3]
%   v : 3D vector to rotate (1x3 vector) [vx, vy, vz]
% Output:
%   v_rotated : Rotated 3D vector (1x3 vector) [vx', vy', vz']

    % Convert vector to a pure quaternion (0, vx, vy, vz)
    v_quat = [0, v(1), v(2), v(3)];
    
    % Calculate q * v_quat
    qv = customQuatMultiply(q, v_quat);
    
    % Calculate conjugate of q
    q_conjugate = [q(1), -q(2), -q(3), -q(4)];
    
    % Calculate the rotated vector quaternion as q * v_quat * q_conjugate
    qv_rotated = customQuatMultiply(qv, q_conjugate);
    
    % Extract the rotated vector part (discard the scalar part)
    v_rotated = qv_rotated(2:4);
end
