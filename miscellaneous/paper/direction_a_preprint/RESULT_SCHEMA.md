# Result identity and scope

Every record must identify the experiment/stage, configuration hash, source-code
hashes, room dimensions, microphone/source coordinates, direction, source/noise
seed identities, sampling rate, frame length, source prehistory, arrival
construction, reflection state, estimator settings, and evaluation subset.

Per-frame output retains record ID, frame index, estimated and true azimuth,
signed wrapped error, feasible-bound status, and failure status. A physical scene
is a particular room/array/source placement. Repeated random source records in
one scene are not additional independent rooms. Paired variants share explicitly
identified source/noise records. Prediction records use separate seed identities.

RNG streams derive from SHA-256 of a serialized experiment/scene/record identity,
converted to a NumPy SeedSequence. They do not depend on process dispatch order
or the Python randomized hash function. Source and noise have distinct labels.

The direct-path stage uses analytical delays and deterministic harmonic signals
for verification. These records are distinct from the later stochastic room
campaign. No hardware performance is inferred.
