% PUMA (Phase Unwrapping via MAxflow) 
%   demo4 - High phase rate Gaussian Hill with a non vertical and non horizontal 
%   alined sector set to zero. 

%   The clique potential is given by  V(x)= |Q2p(x)|^2 where Q2p is the 
%   quantization function; the employed cliques are
%   given by vectors [1 0], [1 1], and [-1 1].

%   Notice: the error image rendered at the end of the script represents
%   the difference between the original (not wrapped) image and the PUMA
%   unwrapped solution.

%   For further details about using PUMA please see puma_ho.m file. See 
%   also: J. Bioucas-Dias and G. Valadão, "Phase Unwrapping via Graph Cuts"
%   IEEE Transactions Image Processing, 2007 (to appear).

% José Bioucas-Dias and Gonçalo Valadão (2007)
% 
% data generation


M=150;
N=100;

mx=75; my=50;

load maskrotnotcenter;
maskrotnotcenter = fliplr(maskrotnotcenter);

% build Gaussian elevation
z=gaussele(M,N,14*pi,10,15).*maskrotnotcenter;
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
cliques = [1 0; 1 1; -1 1];
potential.quantized = 'no';
potential.threshold = 0.5; 

[unwph,iter,erglist] = puma_ho(eta,p,'potential',potential,'cliques',cliques);

figure;
surfl(unwph);shading interp; colormap(gray);
title('Puma solution');

figure; imagesc(z-unwph)
colormap(gray);
title('Error image');


