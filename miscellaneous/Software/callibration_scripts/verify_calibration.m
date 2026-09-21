% Add reference and test dataset filepaths below
ref_data = readmatrix('');
test_data = readmatrix('');

t = (0:length(ref_data)-1)/16000;

figure;
subplot(2,1,1);
plot(t, ref_data, 'b'); hold on;
plot(t, test_data, 'r');

nfft = 2048;
RefFFT = abs(fft(ref_data,nfft));
TestFFT = abs(fft(test_data,nfft));
faxis = (0:nfft-1)*(16000/nfft);

subplot(2,1,2);
plot(faxis,20*log10(RefFFT),'b'); hold on;
plot(faxis,20*log10(TestFFT),'r');
xlim([0 8000]);

corr_val = corr(ref_data,test_data);
fprintf('Correlation = %.3f\n', corr_val);
