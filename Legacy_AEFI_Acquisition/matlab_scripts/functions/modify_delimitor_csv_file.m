% Objectif : Modifier le délimiteur du fichier csv pour pouvoir ouvrir
% simplement avec Excel

function modify_delimitor_csv_file()
    % Fichier d'acquisition par défaut
    default_file = 'C:\Users\saluden231\Nextcloud2\ASSOCE\Banc de test\Banc de test II\Acquisitions\Data\2024-07-16 Acquisitions Test Projection Angulaire\240717_123431_Cylinder_1000_ydir_imaglabview_E_all_12x144.csv';
    
    % Sélection du fichier à modifier (si besoin)
    [file, path] = uigetfile('*.csv', 'Sélectionnez le fichier CSV:', default_file);
    
    % Utiliser le fichier par défaut si aucun fichier n'est sélectionné
    if isequal(file, 0)
        fprintf('Aucun fichier sélectionné. Utilisation du fichier par défaut.\n');
        full_file_path = default_file;
    else
        full_file_path = fullfile(path, file);
        fprintf('Fichier sélectionné : %s\n', full_file_path);
    end
    
    % Choisir le type de conversion
    conversion_type = questdlg('Choisissez le type de conversion de délimiteur :', ...
                               'Conversion de délimiteur', ...
                               '; vers ,', ', vers ;', '; vers ,');
    
    % Définir les délimiteurs à remplacer selon le choix
    if strcmp(conversion_type, '; vers ,')
        from_delimiter = ';';
        to_delimiter = ',';
    elseif strcmp(conversion_type, ', vers ;')
        from_delimiter = ',';
        to_delimiter = ';';
    else
        fprintf('Aucune option de conversion sélectionnée. Opération annulée.\n');
        return;
    end
    
    % Lire le fichier CSV en ignorant la première ligne
    fid = fopen(full_file_path, 'r');
    if fid == -1
        error('Erreur lors de l''ouverture du fichier.');
    end
    
    % Lire toutes les données du fichier, ligne par ligne
    file_data = textscan(fid, '%s', 'Delimiter', '\n'); % Lire tout le contenu en texte brut
    fclose(fid);
    
    % Supprimer la première ligne
    file_data = file_data{1}; % Convertir la cellule en array de chaînes
    file_data(1) = [];        % Supprimer la première ligne
    
    % Remplacer les délimiteurs en fonction du choix de conversion
    for i = 1:length(file_data)
        file_data{i} = strrep(file_data{i}, from_delimiter, to_delimiter); % Remplacer les délimiteurs
    end
    
    % Sauvegarder le fichier modifié (nouveau fichier)
    output_file = fullfile(path, ['modified_' file]); % Créer un nom pour le fichier modifié
    fid_out = fopen(output_file, 'w');
    
    if fid_out == -1
        error('Erreur lors de la création du fichier de sortie.');
    end
    
    % Écrire les nouvelles données dans le fichier
    for i = 1:length(file_data)
        fprintf(fid_out, '%s\n', file_data{i});
    end
    
    fclose(fid_out);
    
    fprintf('Le fichier a été modifié et sauvegardé sous : %s\n', output_file);
end
