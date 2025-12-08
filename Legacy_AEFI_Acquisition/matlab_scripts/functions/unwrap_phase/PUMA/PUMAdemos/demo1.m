% PUMA (Phase Unwrapping via MAxflow) 
%   demo1 - High phase rate Gaussian Hill

%   The clique potential is given by  V(x)= |Q2p(x)|^2 where Q2p is the 
%   quantization function; the employed cliques are
%   given by vectors [0 1] and [1 0].

%   For further details about using PUMA please see puma_ho.m file. See 
%   also: J. Bioucas-Dias and G. Valadão, "Phase Unwrapping via Graph Cuts"
%   IEEE Transactions Image Processing, 2007 (to appear).

% José Bioucas-Dias and Gonçalo Valadão (2007)
clear all
close all
% data generation
M=100;
N=100;
z1=gaussele(M,N,14*pi,10,15); 
% generate insar pair according to model (2002, TIP, vol. 11, no 4.)
co=0.95;	% noise (coherence: co = 1 => no noise; co = 0 => only noise (no signal))
[x1 x2] = insarpair_v2(ones(M), co*ones(M), z1, 0);	
% compute interferogram 
eta  = angle(x1.*conj(x2));	
xx = 1:100;
yy = xx;
hold off
colormap(gray);
imagesc(xx,yy,eta)
title('Interferogram');
drawnow;

% PUMA processing
p=2; % Clique potential exponent
figure;
[unwph,iter,erglist] = puma_ho(eta,p);

figure;
surfl(unwph);shading interp; colormap(gray);
title('Puma solution');


imagesc(ephas2(:,:,3))