function [data,yi] = ReprocData(path,fields,info,limy,mode,delay_ms,varargin)
global colors;
fprintf('  Reprocess images for %s fields from *_all.csv files\n',fields); tic



% Get raw data
if ~exist(path,'file'), fprintf('File not found at location:\n %s\n',path); data = []; yi = []; return; end
rawdata = importdata(path,',');
scan  = rawdata(end,:);

% Detect start/stop scans
% fprintf(' Get start/stop indexes corresponding to scanning parts\n')
jump = gradient(scan);     
scan_start = find(jump == -0.5 & scan == 0);
scan_stop = find(jump == 0.5 & scan == 0);
xscan = max(length(scan_start),length(scan_stop));
% if scan_start dimension is smaller by one, consider 1 as first start.
if length(scan_start) < length(scan_stop)
    scan_start = [1,scan_start];
end

if ~isempty(varargin)
    if length(varargin) == 1
        yscan = varargin{1};
        fprintf('  NY set to %i\n',yscan)
    end
else
    yscan = round(mean(scan_stop-scan_start));
    fprintf('  Average number of data along Y direction is %i\n',yscan)
end

yi = limy(1) + diff(limy)*(0:1/(yscan-1):1);
switch mode
    case 1
        yyi = repmat(yi,xscan,1);
    case 2
        % If mode 2 (S), the coordinates along y direction must be reverse
        % every two rows
        yyi = repmat([yi;flip(yi)],ceil(xscan/2),1);
        if (size(yyi,1)>xscan), yyi(end,:) = []; end
end

% figure(10)
% ni = 1 : length(scan);
% plot(ni,scan,'b-')
% hold on
% plot(ni,jump,'g-')
% plot(ni(scan_start),scan(scan_start),'ro')
% plot(ni(scan_stop),scan(scan_stop),'mo')
% hold off

for k = 1 : length(fields)
    % Sort data per fields (M: Magn., A:Acc., G:Gyro., L:Lidar)
    fi = fields(k);
    
    % Get column and sign correction from info
    col = abs(info.(fi));
    sig = sign(info.(fi));    
   
    clear tmp;
    for j = 1 : length(col)
        if (length(col) == length(info.t))
            colt = info.t(j);
        else
            colt = info.t;
        end
        t     = rawdata(colt,:);
        field = rawdata(col(j),:);

        % Considering a constant speed
        for i = 1 : xscan
            t_scan = t(scan_start(i):scan_stop(i)) - t(scan_start(i));            
            d_scan = limy(1) + diff(limy)*(t_scan-0.001*delay_ms(j))/t_scan(end);
            [d_scan,uni] = unique(d_scan);
            l_scan = field(scan_start(i):scan_stop(i));
            l_scan = l_scan(uni);
            tmp(:,i,j) = sig(j) * interp1(d_scan,l_scan,yyi(i,:),'pchip',NaN);
        end
    end
    
	% Replace NaN values by nearest neighbour
    if sum(isnan(tmp(:))), cprintf(colors{3},"  NaN values found and removed\n");end
    tmp = fillmissing(tmp,'nearest');
    
    % Save to data.(field)    
    data.(fi) = tmp;
end
return