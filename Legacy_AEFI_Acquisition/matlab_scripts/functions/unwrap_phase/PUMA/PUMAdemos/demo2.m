% PUMA (Phase Unwrapping via MAxflow) 
%   demo2 - High phase rate Gaussian Hill with a quarter set to zero.

%   The clique potential is given by  V(x)= |Q2p(x)|^0.5 where Q2p is the 
%   quantization function; the employed cliques are
%   given by vectors [0 1] and [1 0].
%   
%   For further details about using PUMA please see puma_ho.m file. See 
%   also: J. Bioucas-Dias and G. Valadão, "Phase Unwrapping via Graph Cuts"
%   IEEE Transactions Image Processing, 2007 (to appear).

% José Bioucas-Dias and Gonçalo Valadão (2007)
% 
% data generation

M=158;
N=108;
mx=75; my=50;
mask = ones(M,N); mask(1:mx,1:my)=0;
% build Gaussian elevation
z=gaussele(M,N,14*pi,10,15).*mask;
% generate insar pair according to model (2002, TIP, vol. 11, no 4.)
co=1; % noise (coherence: co = 1 => no noise; co = 0 => only noise  (no signal))
[x1 x2] = insarpair(ones(M,N), co*ones(M,N), z, 0);
eta = angle(x1.*conj(x2));

hold off
xx = 1:150;
yy = 1:100;
colormap(gray);
imagesc(xx,yy,eta)
title('Interferogram');
drawnow;


% PUMA processing
p=0.5; % Clique potential exponent
figure;
[unwph,iter,erglist] = puma_ho(eta,p,'verbose',false);


figure;
surfl(unwph);shading interp; colormap(gray);
title('Puma solution');

p = 0.5;
cliques = [1 0; 1 1; -1 1];
potential.quantized = 'no'; potential.threshold = 1;

dim = size(ephas2);
oddx = mod(dim(1),2);
oddy = mod(dim(2),2);
for m = 1
    pha = ephas2(:,:,m);    
    if oddx, pha(dim(1)+1,:) = pha(dim(1),:);end
    if oddx, pha(:,dim(2)+1) = pha(:,dim(2));end
    size(pha)
    pha_unw = puma_ho(pha,p,'potential',potential,'cliques',cliques);
    if oddx, pha_unw(dim(1)+1,:) = [];end
    if oddx, pha_unw(:,dim(2)+1) = [];end    
    ephas2(:,:,m) = pha_unw;
end
imagesc(ephas2(:,:,m))
colormap(jet)