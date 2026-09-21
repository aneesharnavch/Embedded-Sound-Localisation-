% Add reference and test dataset filepaths below
ref_data = readmatrix('');
test_data = readmatrix('');

t = ref_data(:,1);
y_ref = ref_data(:,2);
y_test = test_data(:,2);

f0 = 4000; 
ft = fittype('a*sin(2*pi*f0*x + phi)', ...
    'independent','x','coefficients',{'a','phi'},'problem','f0');
opts = fitoptions(ft);
opts.StartPoint = [max(y_test), 0];
[fitresult, gof] = fit(t, y_test, ft, opts, 'problem', f0);

disp(fitresult);
disp(gof);

figure;
plot(t, y_test, 'b'); hold on;
plot(t, y_ref, 'k--');
plot(t, fitresult(t), 'r');
