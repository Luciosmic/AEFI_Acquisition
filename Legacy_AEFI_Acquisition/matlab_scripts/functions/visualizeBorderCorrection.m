function visualizeBorderCorrection(borderCorrection, compNames)
% VISUALIZEBORDERCORRECTION - Visualise les effets de la correction d'offset de bord
%
% Syntaxe :
%   visualizeBorderCorrection(borderCorrection, compNames)
%
% Entrées :
%   borderCorrection - Structure contenant les données avant et après correction
%   compNames - Noms des composantes (ex: {'X', 'Y', 'Z'})
%
% Description :
%   Cette fonction génère des visualisations pour montrer l'effet de la 
%   correction d'offset appliquée aux bords des images. Elle affiche à la 
%   fois les valeurs avant et après correction, ainsi que des profils 
%   de lignes et colonnes.

    % Vérification de la présence des champs requis
    if ~isfield(borderCorrection, 'dataEreal_orig') || ...
       ~isfield(borderCorrection, 'dataEimag_orig') || ...
       ~isfield(borderCorrection, 'dataEreal_corr') || ...
       ~isfield(borderCorrection, 'dataEimag_corr')
        error('Structure borderCorrection incomplète. Vérifiez les champs requis.');
    end

    % Récupération des données
    dataEreal_beforeCorrection = borderCorrection.dataEreal_orig;
    dataEimag_beforeCorrection = borderCorrection.dataEimag_orig;
    dataEreal_afterCorrection = borderCorrection.dataEreal_corr;
    dataEimag_afterCorrection = borderCorrection.dataEimag_corr;
    
    % Si les noms des composantes ne sont pas fournis, utiliser des valeurs par défaut
    if nargin < 2 || isempty(compNames)
        numComponents = size(dataEreal_beforeCorrection, 3);
        compNames = cell(1, numComponents);
        for i = 1:numComponents
            compNames{i} = ['Comp' num2str(i)];
        end
    end
    
    % Déterminons la dimension des données
    [numRows, numCols, numComponents] = size(dataEreal_beforeCorrection);
    
    % Sélection d'une composante pour la visualisation (par exemple, composante X)
    compToShow = 1; % 1=X, 2=Y, 3=Z
    
    % Génération de figures pour visualiser l'effet de la correction
    figure('Name', 'Correction de Dérive Bidirectionnelle', 'Position', [100, 100, 1200, 800]);
    
    % Avant correction
    subplot(2, 2, 1);
    imagesc(dataEreal_beforeCorrection(:, :, compToShow));
    title(['Composante ', compNames{compToShow}, ' - Réelle - Avant Correction']);
    colorbar;
    xlabel('Colonne');
    ylabel('Ligne');
    
    subplot(2, 2, 2);
    imagesc(dataEimag_beforeCorrection(:, :, compToShow));
    title(['Composante ', compNames{compToShow}, ' - Imaginaire - Avant Correction']);
    colorbar;
    xlabel('Colonne');
    ylabel('Ligne');
    
    % Après correction
    subplot(2, 2, 3);
    imagesc(dataEreal_afterCorrection(:, :, compToShow));
    title(['Composante ', compNames{compToShow}, ' - Réelle - Après Correction Bidirectionnelle']);
    colorbar;
    xlabel('Colonne');
    ylabel('Ligne');
    
    subplot(2, 2, 4);
    imagesc(dataEimag_afterCorrection(:, :, compToShow));
    title(['Composante ', compNames{compToShow}, ' - Imaginaire - Après Correction Bidirectionnelle']);
    colorbar;
    xlabel('Colonne');
    ylabel('Ligne');
    
    % Ajouter un suptitle
    sgtitle('Effet de la Correction de Dérive Bidirectionnelle (Lignes puis Colonnes)');
    
    % Optionnel: Afficher également les profils de quelques lignes et colonnes
    figure('Name', 'Profils de Lignes et Colonnes - Avant/Après Correction', 'Position', [100, 100, 1200, 800]);
    
    % Choisir quelques lignes et colonnes à afficher
    linesToShow = [1, round(numRows/3), round(2*numRows/3), numRows];
    colsToShow = [1, round(numCols/3), round(2*numCols/3), numCols];
    
    % Afficher les profils de lignes
    subplot(2, 2, 1);
    hold on;
    for i = 1:length(linesToShow)
        lineIdx = linesToShow(i);
        plot(1:numCols, dataEreal_beforeCorrection(lineIdx, :, compToShow), 'DisplayName', ['Ligne ' num2str(lineIdx) ' - Avant']);
    end
    hold off;
    title(['Profils de Lignes - Avant Correction - Composante ', compNames{compToShow}]);
    xlabel('Position dans la ligne (colonne)');
    ylabel('Amplitude');
    legend('show', 'Location', 'best');
    grid on;
    
    subplot(2, 2, 2);
    hold on;
    for i = 1:length(linesToShow)
        lineIdx = linesToShow(i);
        plot(1:numCols, dataEreal_afterCorrection(lineIdx, :, compToShow), 'DisplayName', ['Ligne ' num2str(lineIdx) ' - Après']);
    end
    hold off;
    title(['Profils de Lignes - Après Correction - Composante ', compNames{compToShow}]);
    xlabel('Position dans la ligne (colonne)');
    ylabel('Amplitude');
    legend('show', 'Location', 'best');
    grid on;
    
    % Afficher les profils de colonnes
    subplot(2, 2, 3);
    hold on;
    for j = 1:length(colsToShow)
        colIdx = colsToShow(j);
        plot(1:numRows, dataEreal_beforeCorrection(:, colIdx, compToShow), 'DisplayName', ['Colonne ' num2str(colIdx) ' - Avant']);
    end
    hold off;
    title(['Profils de Colonnes - Avant Correction - Composante ', compNames{compToShow}]);
    xlabel('Position dans la colonne (ligne)');
    ylabel('Amplitude');
    legend('show', 'Location', 'best');
    grid on;
    
    subplot(2, 2, 4);
    hold on;
    for j = 1:length(colsToShow)
        colIdx = colsToShow(j);
        plot(1:numRows, dataEreal_afterCorrection(:, colIdx, compToShow), 'DisplayName', ['Colonne ' num2str(colIdx) ' - Après']);
    end
    hold off;
    title(['Profils de Colonnes - Après Correction - Composante ', compNames{compToShow}]);
    xlabel('Position dans la colonne (ligne)');
    ylabel('Amplitude');
    legend('show', 'Location', 'best');
    grid on;
    
    % Affichage des offsets calculés si disponibles
    if isfield(borderCorrection, 'rowOffsets_real') && isfield(borderCorrection, 'colOffsets_real')
        figure('Name', 'Offsets Calculés', 'Position', [100, 100, 1200, 800]);
        
        % Affichage des offsets par colonne (partie réelle)
        subplot(2, 2, 1);
        plot(borderCorrection.colOffsets_real(:, compToShow), 'LineWidth', 1.5);
        title(['Offsets par Colonne - Partie Réelle - Composante ', compNames{compToShow}]);
        xlabel('Numéro de Colonne');
        ylabel('Valeur d''Offset');
        grid on;
        
        % Affichage des offsets par ligne (partie réelle)
        subplot(2, 2, 2);
        plot(borderCorrection.rowOffsets_real(:, compToShow), 'LineWidth', 1.5);
        title(['Offsets par Ligne - Partie Réelle - Composante ', compNames{compToShow}]);
        xlabel('Numéro de Ligne');
        ylabel('Valeur d''Offset');
        grid on;
        
        % Affichage des offsets par colonne (partie imaginaire)
        subplot(2, 2, 3);
        plot(borderCorrection.colOffsets_imag(:, compToShow), 'LineWidth', 1.5);
        title(['Offsets par Colonne - Partie Imaginaire - Composante ', compNames{compToShow}]);
        xlabel('Numéro de Colonne');
        ylabel('Valeur d''Offset');
        grid on;
        
        % Affichage des offsets par ligne (partie imaginaire)
        subplot(2, 2, 4);
        plot(borderCorrection.rowOffsets_imag(:, compToShow), 'LineWidth', 1.5);
        title(['Offsets par Ligne - Partie Imaginaire - Composante ', compNames{compToShow}]);
        xlabel('Numéro de Ligne');
        ylabel('Valeur d''Offset');
        grid on;
        
        sgtitle(['Offsets Calculés pour la Correction - Composante ', compNames{compToShow}]);
    end
    
    % Affichage des statistiques de correction
    for comp = 1:numComponents
        % Calcul de la variance avant/après correction
        varRealBefore = var(dataEreal_beforeCorrection(:,:,comp), [], 'all');
        varRealAfter = var(dataEreal_afterCorrection(:,:,comp), [], 'all');
        varImagBefore = var(dataEimag_beforeCorrection(:,:,comp), [], 'all');
        varImagAfter = var(dataEimag_afterCorrection(:,:,comp), [], 'all');
        
        % Moyenne des offsets appliqués
        meanRowOffsetReal = mean(borderCorrection.rowOffsets_real(:,comp));
        meanColOffsetReal = mean(borderCorrection.colOffsets_real(:,comp));
        meanRowOffsetImag = mean(borderCorrection.rowOffsets_imag(:,comp));
        meanColOffsetImag = mean(borderCorrection.colOffsets_imag(:,comp));
        
        % Affichage des statistiques
        fprintf('\n--- Statistiques de correction pour la composante %s ---\n', compNames{comp});
        fprintf('Partie réelle:\n');
        fprintf('  Offset moyen par ligne: %.4f\n', meanRowOffsetReal);
        fprintf('  Offset moyen par colonne: %.4f\n', meanColOffsetReal);
        fprintf('  Réduction de variance: %.2f%%\n', 100*(1-varRealAfter/varRealBefore));
        
        fprintf('Partie imaginaire:\n');
        fprintf('  Offset moyen par ligne: %.4f\n', meanRowOffsetImag);
        fprintf('  Offset moyen par colonne: %.4f\n', meanColOffsetImag);
        fprintf('  Réduction de variance: %.2f%%\n', 100*(1-varImagAfter/varImagBefore));
    end
    
    % Attendre confirmation de l'utilisateur pour continuer
    disp('Visualisation de la correction de dérive bidirectionnelle. Appuyez sur une touche pour continuer...');
    pause;
    
    % Fermer les figures temporaires
    close all;
end 