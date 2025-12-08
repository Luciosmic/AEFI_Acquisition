function data = GetData(path,fields,info,dim)
% Get raw data
fprintf('Loading data...'); tic;
rawdata = importdata(path,',');
fprintf('Done %3.1fs\n',toc)

for i = 1 : length(fields)
    % Sort data per fields (M: Magn., A:Acc., G:Gyro., L:Lidar)
    fi = fields(i);
    
    % Get column and sign correction from info
    col = abs(info.(fi));
    sig = sign(info.(fi));
    
    % Extract data from rawdata
    if isnan(dim)
        dim = [length(rawdata),1];
    end    
    tmp = zeros([flip(dim),length(col)]);
    for j = 1 : length(col)
        tmp(:,:,j) = sig(j) * reshape(rawdata(col(j),:),flip(dim));
    end
    
    % Save to data.(field)
    data.(fi) = tmp;
end
end