function [field_module, field_phase] = display_module_and_phase(field_real, field_imag, testUnwrapping, usePUMA_HO)
%DISPLAY_MODULE_AND_PHASE Computes the module and phase of the electric field.
%   Inputs:
%     - field_real: Real component of the electric field (3D matrix).
%     - field_imag: Imaginary component of the electric field (3D matrix).
%     - testUnwrapping: Boolean, if true, compares different unwrapping methods and displays results.
%     - usePUMA_HO: Boolean, if true, applies the PUMA-HO phase unwrapping method.
%
%   Outputs:
%     - field_module: The modulus (magnitude) of the electric field.
%     - field_phase: The unwrapped phase of the electric field.

    % Set phase limit based on original script
    phaLim = -pi;  % initial value from the script

    % Compute the modulus and phase
    field_module = abs(complex(field_real, field_imag));

    % Wrap the phase between [-pi, pi]
    field_phase_wrapped = angle(complex(field_real, field_imag));
    field_phase = wrapToPi(field_phase_wrapped);
    field_phase(field_phase < phaLim) = field_phase(field_phase < phaLim) + 2 * pi;

    % Optional unwrapping test
    if testUnwrapping
        field_phase_unwrap_test1 = zeros(size(field_phase_wrapped));
        for j = 1:3
            field_phase_unwrap_test1(:, :, j) = unwrap_phase(field_phase_wrapped(:, :, j));
        end

        field_phase_unwrap_test2 = zeros(size(field_phase_wrapped));
        for j = 1:3
            field_phase_unwrap_test2(:, :, j) = phase_unwrap(field_phase_wrapped(:, :, j));
        end

        % Display comparison of wrapping methods
        figure(101)
        imagesc([field_phase(:, :, 1), field_phase_unwrap_test1(:, :, 1), field_phase_unwrap_test2(:, :, 1); ...
            field_phase(:, :, 2), field_phase_unwrap_test1(:, :, 2), field_phase_unwrap_test2(:, :, 2); ...
            field_phase(:, :, 3), field_phase_unwrap_test1(:, :, 3), field_phase_unwrap_test2(:, :, 3);]);
    end

    % Apply PUMA-HO phase unwrapping if the flag is true
    if usePUMA_HO
        dim = size(field_phase);
        oddx = mod(dim(1), 2);
        oddy = mod(dim(2), 2);
        for m = 1:3
            pha = field_phase(:, :, m);
            if oddx, pha(dim(1)+1, :) = pha(dim(1), :); end
            if oddy, pha(:, dim(2)+1) = pha(:, dim(2)); end
            pha_unw = puma_ho(pha, 5, 'verbose', false);
            if oddx, pha_unw(dim(1)+1, :) = []; end
            if oddy, pha_unw(:, dim(2)+1) = []; end
            field_phase(:, :, m) = pha_unw;
        end
    end
end
