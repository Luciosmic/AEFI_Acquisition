%INVGRADIENT Basically the opposite of gradient(), aka Inverse Gradient.
%   F_bar = INVGRADIENT(dFx,dFy) reverses GRADIENT(F), where unit  
%   spacing is assumed.
%   F_bar = INVGRADIENT(dFx,dFy,H), where H is scalar, uses H as the
%   spacing between points.
%   F_bar = INVGRADIENT(dFx,dFy,Hx,Hy) is basically the same, except that
%   both x- and y-spacings are specified.
%   Obviously, the DC offset of the integrated function is arbitrary. Also,
%   INVGRADIENT is limited to 2-dimensions at the moment, ie no
%   3-dimensional matrices, or vectors. If dFx and dFy aren't
%   self-consistent then no exact solution can be integrated. In this case
%   the optimal solution, in the least squares sense, will be found. So 
%   if you do F_bar = INVGRADIENT(dFx,dFy), F_bar will be found such that 
%   doing [dFx_ dFy_] = GRADIENT(F_bar) will give you dFx_ and dFy_ that 
%   are as close as possible to the original dFx and dFy.
%  
%   Patrick Lu
%   April 5, 2005
%   If this doesn't work right, email patlu@nospam.stanford.edu, w/o the nospam.

function F_bar = invgradient(dFx,dFy,varargin)
[rows cols] = size(dFx);
if(length(varargin)==0)
    xspacing = 1;
    yspacing = 1;
elseif(length(varargin)==1)
    xspacing = varargin{1};
    yspacing = varargin{1};
else
    xspacing = varargin{1};
    yspacing = varargin{2};
end

if (rows<3 | cols < 3)
    fprintf('Please keep the input size at least 3x3\n');    
end
%create Gx, which takes the x-derivative such that F*Gx = dFx
Gx = [-1; 1; zeros(cols-2,1)];

middle_column = [-.5;0;.5;zeros(cols-3,1)];
for k = 1:cols-2

    Gx = [Gx,middle_column]; 
    %permute
    middle_column=circshift(middle_column,1);
end
Gx = [Gx, [zeros(cols-2,1); -1; 1]];
Gx = Gx/xspacing;


%create Gy, which takes the y-derivative such that Gy*F = dFy
Gy = [-1, 1, zeros(1,rows-2)];
middle_row = [-.5,0,.5,zeros(1,rows-3)];
for k=1:rows-2
    Gy = [Gy;middle_row];
    %permute
    middle_row=circshift(middle_row,[0 1]);
end
Gy = [Gy; [zeros(1,rows-2),-1,1]];
Gy = Gy/yspacing;


%put them into G2
G2 = [];
for k = 1:cols
    G2_row = [Gx(:,k) zeros(cols,rows-1)];
    G2_row = reshape(G2_row',1,rows*cols);
    for l=1:rows
        G2 = [G2;G2_row];
        G2_row = circshift(G2_row,[0 1]);
    end
end

G2_2 = [];

for k = 1:cols
    G2_2 = blkdiag(G2_2,Gy);
end

G2 = [G2;G2_2];

F_bar = pinv(G2)*[reshape(dFx,rows*cols,1);reshape(dFy,rows*cols,1)];
F_bar = reshape(F_bar,rows,cols);