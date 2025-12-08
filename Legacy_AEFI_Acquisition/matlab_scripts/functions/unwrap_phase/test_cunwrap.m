% test_cunwrap.m
%
% Matlab script to test Costantini's unwrapping
% Author: Bruno Luong <brunoluong@yahoo.com>
% History:
%   Orginal: 27-Aug-2009

Phi = peaks(100);
Phi(:,end)=[];

% Add uniform random noise +/- 17 degree
Phi = Phi+0.6*(rand(size(Phi))-0.5);

% Salt/peper noise
margin = 3; % costantini does not like noise in the border
badfraction = 3e-2; % 1-3 percent
nsp = floor(badfraction*numel(Phi));
y = margin + ceil(rand(1,nsp)*(size(Phi,1)-2*margin));
x = margin + ceil(rand(1,nsp)*(size(Phi,2)-2*margin));
idx = sub2ind(size(Phi),y,x);
Phi(idx) = Phi(idx) + pi*randn(size(idx));

% Wrapped phase
Psi = mod(Phi+pi,2*pi)-pi;

% Unwrap in 4 blocks
[PhiCostantini] = cunwrap(Psi, struct('RoundK',true,'maxblocksize',60));

% Graphic
fig=figure(1);
clf(fig);

ax=subplot(1,2,1,'Parent',fig);
surf(ax,Psi);
title(ax,'Wrapped');
ax=subplot(1,2,2,'Parent',fig);
surf(ax,PhiCostantini);
title(ax,'Costantini');
