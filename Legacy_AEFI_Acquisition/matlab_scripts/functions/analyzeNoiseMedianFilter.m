function analyzeNoiseMedianFilter(ereal, eimag, xcm, ycm, automaticReport, jsonname, pathSave, skipNoiseAnalysis)
    % Author : Matthieu Roblin & Luis Saluden
    % Date : 2024-10-19
    % ANALYZENOISEMEDIAN FILTER Displays noise images based on a median filter.
    % This function calculates the noise for both real and imaginary fields,
    % displays them, and optionally saves the figures based on the automaticReport flag.
    global colors; % yellow, pink, red, blue, orange, green, purple, cyan, green2
    colors = {[255,255,102], [255,153,255], [255,051,051], [102,178,255], ...
        [255,153,051],[102,255,102],[178,102,255],[102,255,255],[154,205,50]};


    fprintf("o) Noise analysis: ");
    fprintf("Analyse du bruit :");

    if ~skipNoiseAnalysis
        for ni = 1:2
            field = (ni == 1) * ereal + (ni == 2) * eimag; % Select the appropriate field
            nm = (ni == 1) * 'real' + (ni == 2) * 'imag'; % Set the name
            
            figure(3 + ni);
            tiledlayout(2, 3, 'Padding', 'none', 'TileSpacing', 'compact');

            % Calculate noise and display images
            for j = 1:3
                noise(:,:,j) = field(:,:,j) - medfilt2(field(:,:,j), 'symmetric');
                nexttile;
                imagesc(xcm, ycm, noise(:,:,j));
                axis image;
                xlabel('X_0 [cm]');
                ylabel('Y_0 [cm]');
                caxis([-0.5, 0.5]);
                set(gca, 'Ydir', 'normal');
                c = colorbar;
                title(sprintf('%s %s', nm, xyz(j)));
                c.Label.String = 'V/m';
            end

            % Plot standard deviation of noise
            colormap hsv;
            noise_mx = 0.2 * ceil(max(max(squeeze(std(noise)))) / 0.2);
            for j = 1:3
                nexttile;
                plot(xcm, std(noise(:,:,j)), 'x-', 'Linewidth', 1.5);
                xlabel('X_0 [cm]');
                ylabel('Standard Deviation [V/m]');
                ylim([0, noise_mx]);
            end

            % Set figure properties
            set(gcf, 'units', 'normalized', 'Position', [0.0, 0.1, 1.0, 0.8]);
            set(findall(gcf, '-property', 'FontSize'), 'FontSize', 13);
            drawnow;

            % Save the figure if automatic reporting is enabled
            if automaticReport
                exportgraphics(gcf, fullfile(pathSave, strrep(jsonname, '.json', sprintf('_noise_%s.jpg', nm))));
            end
        end
        cprintf(colors{6}, "done\n");
    else
        cprintf(colors{5}, "skipped\n");
    end
end
