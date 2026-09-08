% Add reference and test dataset filepaths below
ref_data = readmatrix('');
test_data = readmatrix('');

freq_ref = ref_data(:,1);
resp_ref = ref_data(:,2);
freq_test = test_data(:,1);
resp_test = test_data(:,2);

fs = 16000;
fc = 4000;
trans_bw = 1000;
ripple_db = 60;

if ripple_db > 50
    beta = 0.1102*(ripple_db - 8.7);
elseif ripple_db >= 21
    beta = 0.5842*(ripple_db - 21)^0.4 + 0.07886*(ripple_db - 21);
else
    beta = 0;
end

M = ceil((ripple_db - 8) / (2.285*(2*pi*trans_bw/fs)));
fprintf('Beta = %.3f\n', beta);
fprintf('Order M = %d\n', M);
fprintf('Normalized cutoff = %.3f\n', fc/(fs/2));

b = fir1(M, fc/(fs/2), kaiser(M+1, beta));
freqz(b,1,1024,fs);
