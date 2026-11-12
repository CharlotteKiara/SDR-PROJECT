# IEEE 802.11 OFDM Receiver – SDR Project

## Project Overview

The objective of this project is to study and progressively implement an **IEEE 802.11a/g/p OFDM receiver using GNU Radio**.

The work is based on the article:

> B. Bloessl, M. Segata, C. Sommer and F. Dressler, *“An IEEE 802.11a/g/p OFDM Receiver for GNU Radio”*.

The receiver is constructed and analysed progressively following the weekly project guide.

The first three weeks focus on the synchronization part of the receiver:

- **Week 1:** STF autocorrelation and frame-detection metric
- **Week 2:** frame detection with `WiFi Sync Short`
- **Week 3:** `WiFi Sync Long`, carrier frequency offset correction and delayed input

The experiments use recorded IEEE 802.11 baseband signals provided for the project.

Our main recording is:

`Sample1_20MHz_Channel36.bin`

with a sample rate of:

`20 MHz`

For most experiments, only the **first 2,000,000 samples** are processed in order to keep the execution time reasonable and ensure that results obtained in different weeks can be compared using exactly the same signal segment.

---

# Week 1 – STF Autocorrelation and Frame Detection Metric

## Objective

The objective of Week 1 was to understand how an IEEE 802.11 receiver can detect the beginning of a possible frame using the **Short Training Field (STF)**.

The STF is located at the beginning of an IEEE 802.11 frame and contains a highly repetitive structure.

This repetition can be detected using autocorrelation.

The main objectives were therefore to:

- understand the structure of the STF;
- understand why a delay of 16 samples is used;
- implement the autocorrelation metric described in the reference article;
- normalize the autocorrelation using the received signal power;
- observe the resulting detection plateau;
- analyse the signal in the time and frequency domains.

---

## STF periodicity

The IEEE 802.11 Short Training Field contains a sequence that repeats every **16 samples**.

Therefore, during the STF:

`r[n] ≈ r[n+16]`

This property can be detected by comparing the received signal with a delayed copy of itself.

The received signal is therefore divided into two branches:

1. the original signal;
2. the same signal delayed by 16 samples.

One branch is complex-conjugated and both branches are multiplied.

This produces a correlation between samples separated by 16 samples.

---

## Autocorrelation

The autocorrelation used for frame detection can be represented as:

**a[n] = Σ r[n+k] × r*[n+k+16]**

where `*` represents the complex conjugate.

When the signal contains the STF, samples separated by 16 positions are similar.

The magnitude of the autocorrelation therefore becomes large.

Outside the STF, the signal is not necessarily periodic every 16 samples, so the correlation is generally lower.

---

## Power estimation

The received signal power is also calculated.

It can be represented as:

**p[n] = Σ |r[n+k]|²**

This value is used to normalize the autocorrelation.

Without normalization, the correlation magnitude would strongly depend on the received signal amplitude.

---

## Normalized detection metric

The final frame-detection metric is:

**c[n] = |a[n]| / p[n]**

This normalization makes the detector less dependent on the absolute received signal power.

When the STF is present, `c[n]` becomes large and forms a plateau.

This plateau is later used by `WiFi Sync Short` to detect a possible IEEE 802.11 frame.

---

## GNU Radio implementation

The Week 1 GNU Radio flowgraph implements the detection metric using basic signal-processing blocks.

The important parameters are:

- Sample rate: `20 MHz`
- STF periodicity / delay: `16 samples`
- Autocorrelation moving-average window: `48 samples`
- Power moving-average window: `64 samples`

The denominator window is larger because it corresponds to:

`48 + 16 = 64 samples`

The normalized metric is then obtained by dividing the magnitude of the autocorrelation by the estimated signal power.

---

## Observations

When the recorded signal is processed, the normalized autocorrelation increases when an STF is present.

A plateau can therefore be observed around the beginning of possible IEEE 802.11 frames.

With the selected window sizes, an ideal constant-power repeated sequence would approximately produce:

`48 / 64 = 0.75`

However, the real recorded signal contains noise, channel effects and amplitude variations, so the measured plateau is not expected to be perfectly flat or exactly equal to 0.75.

The important observation is the appearance of a region where the normalized autocorrelation remains significantly higher than outside the STF.

---

## Time and frequency analysis

The received signal was also observed using GNU Radio time and frequency sinks.

The time-domain representation allows us to observe changes in the received signal amplitude.

The frequency-domain representation shows the occupied Wi-Fi channel and confirms that the recorded signal contains OFDM transmissions.

These visualizations are useful for understanding the signal, but frame detection itself is based on the STF autocorrelation.

---

## Week 1 conclusion

Week 1 showed that the periodic structure of the Short Training Field can be exploited for frame detection.

The 16-sample repetition allows the receiver to compute a normalized autocorrelation metric.

The final metric:

**c[n] = |a[n]| / p[n]**

produces a plateau when the STF is present.

This metric is used by the synchronization block studied during Week 2.

---

# Week 2 – WiFi Sync Short

## Objective

The objective of Week 2 was to understand the role of the `WiFi Sync Short` block and investigate how its detection parameters affect frame detection.

The main points studied were:

- the role of `WiFi Sync Short`;
- the meaning of the detection threshold;
- the effect of changing the threshold;
- the role of `Min Plateau`;
- the limitations of autocorrelation-based frame detection;
- a practical case where detection fails.

---

## Role of WiFi Sync Short

`WiFi Sync Short` receives the normalized autocorrelation metric generated using the STF.

The block searches for a sufficiently long region where the correlation metric exceeds a predefined threshold.

When the detection conditions are satisfied, the block identifies a possible frame start and generates a:

`wifi_start`

tag.

This tag is used by the following synchronization stages of the receiver.

---

## Detection threshold

The threshold determines how large the normalized autocorrelation must be before the signal is considered a possible STF.

A **low threshold** makes the detector more permissive.

This increases the number of detections, but some of these detections may correspond to unwanted triggers rather than actual frame starts.

A **high threshold** makes the detector more restrictive.

This reduces unwanted triggers, but if the threshold becomes too high, valid frames can also be missed.

The objective is therefore not simply to maximize the number of detections.

---

## Min Plateau

`Min Plateau` determines how long the correlation metric must remain above the threshold before a frame start is accepted.

For our experiments:

`Min Plateau = 2`

This value was kept constant during the threshold experiment so that only one parameter was modified at a time.

---

## Experimental configuration

The same signal segment was used for every threshold value:

- Input: `Sample1_20MHz_Channel36.bin`
- Sample rate: `20 MHz`
- Samples processed: first `2,000,000`
- Autocorrelation window: `48`
- Power window: `64`
- `Min Plateau = 2`

Only the detection threshold was changed.

The number of generated `wifi_start` tags was counted for each run.

---

## Threshold experiment

The following results were obtained:

| Threshold | wifi_start detections |
| ---: | ---: |
| 0.20 | 3089 |
| 0.30 | 1205 |
| 0.40 | 573 |
| 0.50 | 502 |
| 0.56 | 481 |
| 0.60 | 452 |
| 0.70 | 334 |
| 0.75 | 72 |
| 0.80 | 0 |

---

## Analysis of the results

The number of detections decreases when the threshold increases.

At very low thresholds, the detector becomes highly permissive.

For example:

`Threshold = 0.20 → 3089 detections`

Increasing the threshold strongly reduces the number of triggers.

Around the reference operating region:

- `0.50 → 502 detections`
- `0.56 → 481 detections`
- `0.60 → 452 detections`

The change is relatively gradual.

However, a strong decrease appears when approaching the theoretical STF correlation level:

- `0.70 → 334 detections`
- `0.75 → 72 detections`
- `0.80 → 0 detections`

This shows that a threshold that is too restrictive can completely prevent frame detection.

---

## Why use 0.56?

The reference configuration of the current implementation uses:

`Threshold = 0.56`

Our experiment does not prove that `0.56` is mathematically optimal.

Determining an optimal threshold would require knowing the true positions of all transmitted frames and comparing true detections, false detections and missed frames.

However, the experiment shows that `0.56` lies in a useful operating region for this recording.

It produces significantly fewer triggers than very low thresholds while remaining far from the complete detection failure observed at `0.80`.

For the following weeks, we therefore keep:

- `Threshold = 0.56`
- `Min Plateau = 2`

---

## Limitations of the detection method

Autocorrelation-based frame detection is computationally efficient, which is important because it operates continuously at the full sample rate.

However, it also has limitations.

### Threshold sensitivity

The detector depends on the selected threshold.

A threshold that is too low can generate many unwanted detections, while a threshold that is too high can miss frames.

### Noise and channel conditions

Noise, multipath propagation and signal attenuation can modify the correlation plateau.

The plateau observed with a real signal is therefore not perfectly flat.

### Fixed forwarding behaviour

After detecting a frame, the synchronization stage forwards a fixed amount of data.

This limits the maximum frame size that can be handled by the implementation.

Another frame arriving while the block is already forwarding samples may also be missed.

### Autocorrelation versus matched filtering

Matched filtering using a known STF sequence could provide more robust detection.

However, it would require significantly more computations at the full sample rate.

Autocorrelation is therefore used as an efficient first synchronization stage.

---

## Practical failure case

The threshold experiment provides a direct failure case.

With:

`Threshold = 0.80`

the detector generated:

`0 wifi_start detections`

for the tested signal segment.

This demonstrates that increasing the threshold too much can prevent the receiver from detecting any frame.

---

## Week 2 conclusion

Week 2 showed how `WiFi Sync Short` transforms the STF autocorrelation metric into frame-start detections.

The threshold controls the trade-off between permissive and restrictive detection.

For our signal:

- low thresholds produced many detections;
- increasing the threshold progressively reduced the number of detections;
- `Threshold = 0.80` completely prevented detection.

The reference configuration retained for the following weeks is:

- `Threshold = 0.56`
- `Min Plateau = 2`

With this configuration and the first 2,000,000 samples:

**481 possible frame starts were detected.**

---

# Week 3 – WiFi Sync Long and Frequency Offset Correction

## Objective

The objective of Week 3 was to understand the second synchronization stage of the receiver.

The main topics were:

- the role of `WiFi Sync Long`;
- the origin of carrier frequency offset;
- coarse frequency offset estimation using the STF;
- fine frequency offset estimation using the LTF;
- frequency offset correction;
- the purpose of the delayed input;
- the influence of changing the Delay value.

---

## Carrier frequency offset

The transmitter and receiver use independent local oscillators.

In practice, their carrier frequencies are never perfectly identical.

The difference between these frequencies creates a **Carrier Frequency Offset (CFO)**.

A CFO produces a progressive phase rotation in the received complex baseband samples.

If this error is not corrected, it can disturb OFDM demodulation and introduce inter-carrier interference.

The receiver therefore estimates and compensates for this frequency difference before decoding the OFDM symbols.

---

## Coarse CFO estimation with the STF

The first frequency-offset estimate is performed using the STF.

Since the STF repeats every 16 samples, the receiver can compare two samples separated by 16 positions.

The phase difference between these repeated samples contains information about the carrier frequency offset.

The principle can be represented as:

**Δf_short = (1/16) arg(Σ s[n]s*[n+16])**

The conjugate product measures the phase difference between the repeated samples.

The sum improves robustness to noise.

The division by 16 converts the accumulated phase difference into a phase rotation per sample.

In the current receiver implementation, this coarse estimation is performed in `WiFi Sync Short`.

---

## Role of WiFi Sync Long

After the first frame detection and coarse CFO correction, the signal enters `WiFi Sync Long`.

The Long Training Field contains two repeated sequences of 64 samples.

`WiFi Sync Long` uses this known structure to:

- locate the LTF;
- refine the remaining frequency offset;
- determine a more precise synchronization position;
- prepare the samples for OFDM symbol processing.

The detailed symbol-alignment operation is studied in Week 4.

---

## Fine CFO estimation

After the coarse STF-based correction, a residual frequency offset can remain.

The two repeated LTF sequences allow this remaining offset to be estimated more accurately.

A simplified representation is:

**Δf_long = (1/64) arg(P1 P2*)**

where `P1` and `P2` represent the complex correlation values associated with the two LTF repetitions.

The receiver therefore uses two frequency-synchronization stages:

| Stage | Block | Training field | Repetition |
| --- | --- | --- | --- |
| Coarse CFO | `WiFi Sync Short` | STF | 16 samples |
| Fine CFO | `WiFi Sync Long` | LTF | 64 samples |

---

## Frequency offset correction

Once the phase rotation has been estimated, the receiver compensates for it by applying an opposite complex rotation.

The principle is:

**s_corrected[n] = s[n] × exp(-j n Δφ)**

where `Δφ` is the estimated phase rotation per sample.

The purpose is to remove the progressive phase rotation caused by the transmitter/receiver oscillator mismatch.

---

## Why does WiFi Sync Long have two inputs?

`WiFi Sync Long` receives:

- a direct input: `in`
- a delayed input: `in_delayed`

The direct input is used to search for the LTF and determine the synchronization position.

However, the block must examine a certain number of samples before it knows where the correct output should begin.

GNU Radio processes samples continuously and cannot simply go backwards in the stream after making this decision.

For this reason, a second delayed copy of the signal is provided.

The delayed branch preserves earlier samples while the direct branch is being analysed.

---

## Sync Length and Delay

The current reference configuration is:

- `Sync Length = 320 samples`
- `Delay = 320 samples`

The Delay therefore compensates for the synchronization window used by `WiFi Sync Long`.

Once synchronization has been determined using the direct branch, the corresponding earlier samples are still available on the delayed branch.

This allows correctly positioned samples to be forwarded to the following OFDM processing stages.

---

## First Delay experiment – synchronization tags

The first experiment studied whether changing the Delay modifies the synchronization detections.

The configuration remained:

- Input: `Sample1_20MHz_Channel36.bin`
- First `2,000,000` samples
- Sample rate: `20 MHz`
- Threshold: `0.56`
- Min Plateau: `2`
- Sync Length: `320`

Only the external Delay was modified.

Results:

| Delay | Sync Short detections | Sync Long tags |
| ---: | ---: | ---: |
| 160 | 481 | 68 |
| 300 | 481 | 68 |
| 310 | 481 | 68 |
| 320 | 481 | 68 |

The number of Sync Short detections remains constant at **481**, which is expected because the Delay is located after `WiFi Sync Short`.

More interestingly, the number of observed Sync Long tags also remains equal to **68**.

Therefore, simply counting synchronization tags does not reveal the effect of changing the delayed input.

---

## Why the Delay can still matter

Inspection of the synchronization behaviour shows that the direct input is used for synchronization detection.

The delayed input is mainly involved when the synchronized samples are forwarded to the following stages.

Therefore:

**an incorrect Delay can leave the synchronization tag count unchanged while shifting the samples sent downstream.**

To observe this effect, additional OFDM processing blocks were temporarily connected after `WiFi Sync Long`.

---

## Downstream processing experiment

The following chain was used:

`WiFi Sync Long`

↓

`Stream to Vector (64)`

↓

`FFT (64)`

↓

`WiFi Frame Equalizer`

↓

`WiFi Decode MAC`

These blocks are studied in more detail during later weeks.

For Week 3, they were only used to determine whether the samples produced by `WiFi Sync Long` could still be decoded.

---

## Experiment using the first 2,000,000 samples

The Delay was varied while keeping all other parameters constant.

| Delay | Detected | Valid SIGNAL | MAC decoded |
| ---: | ---: | ---: | ---: |
| 290 | 481 | 8 | 0 |
| 300 | 481 | 6 | 0 |
| 310 | 481 | 10 | 0 |
| 314 | 481 | 9 | 0 |
| 318 | 481 | 9 | 1 |
| 320 | 481 | 8 | 1 |
| 322 | 481 | 7 | 1 |
| 326 | 481 | 10 | 0 |
| 330 | 481 | 8 | 1 |
| 334 | 481 | 11 | 0 |
| 336 | 481 | 6 | 0 |
| 338 | 481 | 10 | 0 |
| 340 | 481 | 10 | 0 |
| 350 | 481 | 8 | 0 |
| 360 | 481 | 10 | 0 |

The number of possible frame detections remains equal to **481**.

However, only a very small number of frames from this signal segment are completely decoded.

This demonstrates that:

**a Sync Short detection is not equivalent to a successfully decoded Wi-Fi frame.**

A possible STF can be detected even if later synchronization or decoding stages fail.

Because the first 2,000,000 samples contain too few completely decoded frames to clearly characterize the Delay effect, a supplementary experiment was performed using the complete recording.

---

## Supplementary experiment using the complete recording

The same receiver was run on the complete `Sample1_20MHz_Channel36.bin` recording.

All receiver parameters were kept unchanged.

Only the amount of processed data was increased.

The complete recording produced:

**4357 Sync Short detections**

instead of 481.

This increase is simply because more samples were processed.

It does not indicate an improvement in the detector.

The successful Delay experiments produced:

| Delay | Sync Short detections | CRC-valid decoded frames |
| ---: | ---: | ---: |
| 290 | 4357 | 0 |
| 310 | 4357 | 100 |
| 314 | 4357 | 76 |
| 320 | 4357 | 648 |
| 322 | 4357 | 451 |
| 330 | 4357 | 566 |
| 334 | 4357 | 574 |
| 336 | 4357 | 162 |
| 338 | 4357 | 362 |
| 340 | 4357 | 12 |
| 350 | 4357 | 0 |
| 360 | 4357 | 0 |

Some tested values produced runtime errors and were therefore excluded rather than interpreted as experimental results.

---

## Analysis of the Delay experiment

The number of Sync Short detections remains constant at **4357** for every successful run.

However, the number of CRC-valid decoded frames strongly depends on the Delay.

The reference configuration:

`Delay = 320`

produced:

**648 CRC-valid frames**

In contrast:

- `Delay = 290` → 0 frames
- `Delay = 340` → 12 frames
- `Delay = 350` → 0 frames
- `Delay = 360` → 0 frames

This confirms that the delayed branch affects the samples delivered to the OFDM demodulation stages.

Some values close to 320 still allow a large number of frames to be decoded.

This can be explained partly by the timing tolerance provided by the OFDM cyclic prefix.

The results are not perfectly monotonic because the final decoding also depends on the precise FFT window position, the real propagation channel, synchronization decisions and equalization.

The experiment is therefore not intended to derive an exact mathematical relationship between Delay and decoded frames.

The important result is that an incorrect Delay can prevent successful decoding even when synchronization tags are still generated.

---

## Week 3 conclusion

Week 3 showed that IEEE 802.11 frequency synchronization is performed progressively.

`WiFi Sync Short` uses the STF periodicity to obtain a coarse CFO estimate.

`WiFi Sync Long` then uses the repeated LTF structure to refine the remaining frequency error and prepare the signal for precise OFDM synchronization.

The delayed input is necessary because the block must analyse samples before knowing the correct synchronization position.

The reference configuration is:

- `Sync Length = 320 samples`
- `Delay = 320 samples`

Changing the Delay did not modify the observed synchronization tag counts in our first experiment.

However, downstream decoding showed that an incorrect Delay changes the alignment of the samples sent to the following OFDM processing stages and can strongly reduce or completely prevent successful frame decoding.

For the following weeks, the reference configuration remains:

**Sync Length = 320, Delay = 320**

---

# Current Receiver Configuration

At the end of Week 3, the synchronization part of the receiver can be summarized as:

`Recorded IQ samples`

↓

`STF autocorrelation`

↓

`Normalized detection metric`

↓

`WiFi Sync Short`

↓

`WiFi Sync Long`

↓

`Stream to Vector`

↓

`FFT`

↓

`WiFi Frame Equalizer`

↓

`WiFi Decode MAC`

The main parameters currently used are:

| Parameter | Value |
| --- | --- |
| Sample rate | 20 MHz |
| STF repetition | 16 samples |
| Autocorrelation window | 48 samples |
| Power window | 64 samples |
| Sync Short threshold | 0.56 |
| Min Plateau | 2 |
| Sync Length | 320 samples |
| External Delay | 320 samples |
| FFT length | 64 samples |

---

# Next Step – Week 4

The next step is to study **precise OFDM symbol alignment using the Long Training Field**.

In particular, Week 4 will focus on:

- matched filtering with the known LTF;
- the implementation of the correlation used for symbol alignment;
- Equation 6 of the reference article;
- the reason for the additional 64 samples in Equation 7;
- the role of the `Stream to Vector` block;
- how synchronized samples are converted into 64-sample OFDM symbols before the FFT.

---

# References

1. B. Bloessl, M. Segata, C. Sommer and F. Dressler, *“An IEEE 802.11a/g/p OFDM Receiver for GNU Radio”*, SRIF 2013.

2. A. Aguiar, *Guide to Work through the 802.11a Receiver Article*, Digital Communications SDR Project.

3. `gr-ieee802-11` GNU Radio implementation.
