# 802.11a OFDM System Design Parameters - Week 1

## 1. Core System Parameters
* **Bandwidth:** 20 MHz for IEEE 802.11a/g networks.
* **Sub-carrier spacing:** 312.5 kHz ($20\text{ MHz} / 64$ subcarriers).
* **Number of subcarriers:** A total of 64 subcarriers.
* **IFFT/FFT size:** 64, meaning the system processes vectors of 64 symbols in the frequency domain.
* **Number of data subcarriers:** 48 subcarriers.
* **Number of pilot subcarriers:** 4 subcarriers dedicated to encoding a predefined BPSK constellation for phase offset correction.

---

## 2. Unused Subcarriers
* **Why are there unused subcarriers and where are they located?**
  Unused subcarriers (guard subcarriers and the DC subcarrier) are present to prevent spectral overlap, mitigate inter-channel interference (ICI) with adjacent channels, and avoid DC offset issues at the center frequency. They are located at the edges of the spectrum (guard bands) and at the center (DC subcarrier).

---

## 3. Timing, Sampling, and Symbol Length
* **Sampling rate:** 20 Msps (20 million samples per second) to support a 20 MHz channel bandwidth.
* **OFDM symbol duration:** The useful symbol duration is $3.2\,\mu\text{s}$ (excluding the cyclic prefix). Total symbol duration is $4.0\,\mu\text{s}$.
* **OFDM symbol length (samples):** Each OFDM symbol spans a total of 80 samples.
* **Cyclic prefix length:** 16 samples ($0.8\,\mu\text{s}$), formed by taking the last 16 samples of the FFT block to prevent Inter-Symbol Interference (ISI).

---

## 4. Frame Prefix Sequence
* **Short Preamble Sequence:** Consists of a short training sequence pattern spanning 16 samples that repeats 10 times (total 160 samples, $8\,\mu\text{s}$ duration). It is mainly used for frame detection, AGC, and coarse frequency offset estimation.
* **Long Preamble Sequence:** Consists of a pattern spanning 64 samples that repeats 2.5 times (total 160 samples including CP, $8\,\mu\text{s}$ duration)[cite: 4]. It is used for fine frequency offset estimation and channel estimation/symbol alignment[cite: 3, 4].
