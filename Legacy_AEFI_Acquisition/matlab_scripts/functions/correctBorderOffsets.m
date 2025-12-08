function [dataEreal_corr, dataEimag_corr, borderCorrection] = correctBorderOffsets(dataEreal, dataEimag)
%CORRECTBORDEROFFSETS Corrige les offsets en normalisant par rapport à la première colonne/ligne
%
% Syntaxe :
%   [dataEreal_corr, dataEimag_corr] = correctBorderOffsets(dataEreal, dataEimag)
%   [dataEreal_corr, dataEimag_corr, borderCorrection] = correctBorderOffsets(dataEreal, dataEimag)
%
% Entrées :
%   dataEreal    - Matrice 3D des données réelles [nRows x nCols x nComp]
%   dataEimag    - Matrice 3D des données imaginaires [nRows x nCols x nComp]
%
% Sorties :
%   dataEreal_corr   - Matrice 3D des données réelles corrigées
%   dataEimag_corr   - Matrice 3D des données imaginaires corrigées
%   borderCorrection - Structure contenant les informations de correction

% Validation des entrées
if nargin < 2
    error('Les matrices de données réelles et imaginaires sont requises.');
end

if ~isequal(size(dataEreal), size(dataEimag))
    error('Les matrices de données réelles et imaginaires doivent avoir la même taille.');
end

% Obtenir les dimensions des données
[nRows, nCols, nComp] = size(dataEreal);

% Initialiser les matrices de sortie
dataEreal_corr = zeros(size(dataEreal));
dataEimag_corr = zeros(size(dataEimag));

% Correction pour chaque composante
for comp = 1:nComp
    % Extraire les données pour la composante actuelle
    compDataReal = dataEreal(:,:,comp);
    compDataImag = dataEimag(:,:,comp);
    
    % 1. Normalisation par colonne: soustraire la première colonne de toutes les colonnes
    firstColReal = compDataReal(:,1);
    firstColImag = compDataImag(:,1);
    
    for col = 1:nCols
        compDataReal(:,col) = compDataReal(:,col) - firstColReal;
        compDataImag(:,col) = compDataImag(:,col) - firstColImag;
    end
    
    % 2. Normalisation par ligne: soustraire la première ligne de toutes les lignes
    firstRowReal = compDataReal(1,:);
    firstRowImag = compDataImag(1,:);
    
    for row = 1:nRows
        compDataReal(row,:) = compDataReal(row,:) - firstRowReal;
        compDataImag(row,:) = compDataImag(row,:) - firstRowImag;
    end
    
    % Mettre à jour les données corrigées
    dataEreal_corr(:,:,comp) = compDataReal;
    dataEimag_corr(:,:,comp) = compDataImag;
end

% Préparer la structure de sortie avec les informations de correction
if nargout > 2
    borderCorrection = struct(...
        'dataEreal_orig', dataEreal, ...
        'dataEimag_orig', dataEimag, ...
        'dataEreal_corr', dataEreal_corr, ...
        'dataEimag_corr', dataEimag_corr);
end

end 