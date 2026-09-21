% Add reference and test dataset filepaths below
ref_data = readmatrix('');
test_data = readmatrix('');

dist_ref = unique(ref_data(:,1));
freq_ref = unique(ref_data(:,2));
var_ref = reshape(ref_data(:,3), length(freq_ref), length(dist_ref));

dist_test = unique(test_data(:,1));
freq_test = unique(test_data(:,2));
var_test = reshape(test_data(:,3), length(freq_test), length(dist_test));

figure;
surf(dist_test, freq_test, var_test);
shading interp; colorbar;

[dF, dD] = gradient(var_test);
grad_mag = sqrt(dF.^2 + dD.^2);

figure;
imagesc(dist_test, freq_test, grad_mag);
axis xy; colorbar;
