% PUMA (Phase Unwrapping via MAxflow) 
%   demo3 - Shear Ramp
%   The clique potential is given by  V(x)= |x|^0.5. The employed clique is
%   given by vector [0 1]. 

%   For further details about using PUMA please see puma_ho.m file. See 
%   also: J. Bioucas-Dias and G. Valadão, "Phase Unwrapping via Graph Cuts"
%   IEEE Transactions Image Processing, 2007 (to appear).

% José Bioucas-Dias and Gonçalo Valadão (2007)
% 
% data generation

M=150;
N=100;

%build planes
[X,Y] = meshgrid(0:N-1,0:M-1);
%make discontinuous
mask=ones(M,N); mask(1:M/2,:)=0;
X=X.*mask;
% generate insar pair according to model (2002, TIP, vol. 11, no 4.)
co=1; % noise (coherence: co = 1 => no noise; co = 0 => only noise  (no signal))
[x1 x2] = insarpair(ones(M,N), co*ones(M,N), X, 0);
eta=angle(x1.*conj(x2));

hold off
xx = -M/2-1:M/2;
yy = -N/2-1:N/2;
colormap(gray);
imagesc(eta)
title('Interferogram');
drawnow;

% PUMA processing
p=0.5; % Clique potential exponent
potential.quantized = 'no'; potential.threshold = 0;
cliques = [0 1]; %In this demo our cliques deal with one direction only
figure;
[unwph,iter,erglist] = puma_ho(eta,p,'potential',potential,'cliques',cliques);

figure;
surfl(unwph);shading interp; colormap(gray);
title('Puma solution');





