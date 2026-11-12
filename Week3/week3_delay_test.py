#!/usr/bin/env python3

import argparse
import csv
import time

import numpy as np
import pmt

from gnuradio import blocks, fft, gr
from gnuradio.fft import window

import ieee802_11


# ============================================================
# Count wifi_start tags after WiFi Sync Short
# ============================================================

class TagCounter(gr.sync_block):

    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="wifi_start_counter",
            in_sig=[np.complex64],
            out_sig=[np.complex64],
        )

        self.key = pmt.intern("wifi_start")
        self.count = 0

    def work(self, input_items, output_items):

        n = len(input_items[0])

        # Pass the signal without changing it
        output_items[0][:] = input_items[0]

        # Count wifi_start tags
        tags = self.get_tags_in_window(0, 0, n)

        for tag in tags:
            if pmt.eq(tag.key, self.key):
                self.count += 1

        return n


# ============================================================
# Count messages produced by Decode MAC
# ============================================================

class MessageCounter(gr.basic_block):

    def __init__(self):

        gr.basic_block.__init__(
            self,
            name="decoded_frame_counter",
            in_sig=None,
            out_sig=None,
        )

        self.count = 0

        self.message_port_register_in(
            pmt.intern("in")
        )

        self.set_msg_handler(
            pmt.intern("in"),
            self.handle_message
        )

    def handle_message(self, msg):
        self.count += 1


# ============================================================
# Equalizer type
# ============================================================

def get_equalizer():

    if hasattr(ieee802_11, "LS"):
        return ieee802_11.LS

    return ieee802_11.Equalizer.LS


# ============================================================
# One experiment for one Delay value
# ============================================================

class DelayExperiment(gr.top_block):

    def __init__(self, args, delay_value):

        gr.top_block.__init__(
            self,
            "Week 3 Delay Experiment"
        )

        W = args.window_size

        # ----------------------------------------------------
        # Recorded WiFi signal
        # ----------------------------------------------------

        source = blocks.file_source(
            gr.sizeof_gr_complex,
            args.input_file,
            False
        )

        # Same number of samples as the GRC experiment
        head = blocks.head(
            gr.sizeof_gr_complex,
            args.num_samples
        )

        self.connect(
            source,
            head
        )


        # ====================================================
        # WEEK 1/2 - FRAME DETECTION
        # ====================================================

        delay16 = blocks.delay(
            gr.sizeof_gr_complex,
            16
        )

        conjugate = blocks.conjugate_cc()

        multiply = blocks.multiply_cc(1)

        autocorr_avg = blocks.moving_average_cc(
            W,
            1,
            4000,
            1
        )

        autocorr_mag = blocks.complex_to_mag(1)

        power = blocks.complex_to_mag_squared(1)

        power_avg = blocks.moving_average_ff(
            W + 16,
            1,
            4000,
            1
        )

        divide = blocks.divide_ff(1)


        # WiFi Sync Short
        sync_short = ieee802_11.sync_short(
            args.threshold,
            args.min_plateau,
            False,
            False
        )


        # ----------------------------------------------------
        # Power branch
        # ----------------------------------------------------

        self.connect(
            head,
            power,
            power_avg,
            (divide, 1)
        )


        # ----------------------------------------------------
        # Autocorrelation branch
        # ----------------------------------------------------

        self.connect(
            head,
            delay16,
            conjugate,
            (multiply, 1)
        )

        self.connect(
            head,
            (multiply, 0)
        )

        self.connect(
            multiply,
            autocorr_avg,
            autocorr_mag,
            (divide, 0)
        )


        # ----------------------------------------------------
        # Inputs of WiFi Sync Short
        # ----------------------------------------------------

        self.connect(
            delay16,
            (sync_short, 0)
        )

        self.connect(
            autocorr_avg,
            (sync_short, 1)
        )

        self.connect(
            divide,
            (sync_short, 2)
        )


        # ----------------------------------------------------
        # Count Sync Short detections
        # ----------------------------------------------------

        self.detected = TagCounter()

        self.connect(
            sync_short,
            self.detected
        )


        # ====================================================
        # WEEK 3 - WIFI SYNC LONG
        # ====================================================

        long_delay = blocks.delay(
            gr.sizeof_gr_complex,
            delay_value
        )

        sync_long = ieee802_11.sync_long(
            args.sync_length,
            False,
            False
        )


        # Direct input of Sync Long
        self.connect(
            self.detected,
            (sync_long, 0)
        )


        # Delayed input of Sync Long
        self.connect(
            self.detected,
            long_delay,
            (sync_long, 1)
        )


        # ====================================================
        # RECEIVER AFTER SYNC LONG
        #
        # These blocks are used only to check if the frame
        # remains usable after changing the Delay.
        # ====================================================


        # Convert the synchronized stream into OFDM symbols
        stream_to_vector = blocks.stream_to_vector(
            gr.sizeof_gr_complex,
            64
        )


        # 64-point FFT
        fft_block = fft.fft_vcc(
            64,
            True,
            window.rectangular(64),
            True,
            1
        )


        # Channel equalization / SIGNAL processing
        equalizer = ieee802_11.frame_equalizer(
            get_equalizer(),
            args.frequency,
            args.samp_rate,
            False,
            False
        )


        # MAC decoding
        decode_mac = ieee802_11.decode_mac(
            False,
            False
        )


        # Count decoded frames
        self.decoded = MessageCounter()


        # ----------------------------------------------------
        # Receiver connections
        # ----------------------------------------------------

        self.connect(
            sync_long,
            stream_to_vector
        )

        self.connect(
            stream_to_vector,
            fft_block
        )

        self.connect(
            fft_block,
            equalizer
        )

        self.connect(
            equalizer,
            decode_mac
        )


        # Decode MAC produces messages
        self.msg_connect(
            (decode_mac, "out"),
            (self.decoded, "in")
        )


# ============================================================
# Run one Delay value
# ============================================================

def run_test(args, delay_value):

    tb = DelayExperiment(
        args,
        delay_value
    )

    tb.start()
    tb.wait()

    # Small wait to make sure all messages are processed
    time.sleep(0.2)

    return (
        tb.detected.count,
        tb.decoded.count
    )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser()


    # Input file
    parser.add_argument(
        "--input-file",
        required=True
    )


    # Delay values to test
    parser.add_argument(
        "--delays",
        type=int,
        nargs="+",
        default=[
            290,
            300,
            310,
            314,
            318,
            320,
            322,
            326,
            330,
            334,
            336,
            338,
            340,
            350,
            360
        ]
    )


    # WiFi Sync Long parameter
    parser.add_argument(
        "--sync-length",
        type=int,
        default=320
    )


    # Sampling rate
    parser.add_argument(
        "--samp-rate",
        type=float,
        default=20e6
    )


    # Week 1 autocorrelation window
    parser.add_argument(
        "--window-size",
        type=int,
        default=48
    )


    # Same 2 million samples as the GRC
    parser.add_argument(
        "--num-samples",
        type=int,
        default=2000000
    )


    # WiFi Sync Short parameters
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.56
    )

    parser.add_argument(
        "--min-plateau",
        type=int,
        default=2
    )


    # Channel 36 = 5.18 GHz
    parser.add_argument(
        "--frequency",
        type=float,
        default=5.18e9
    )


    # Output CSV
    parser.add_argument(
        "--csv",
        default="week3_delay_results.csv"
    )


    args = parser.parse_args()


    # ========================================================
    # Run experiments
    # ========================================================

    results = []

    print()
    print("Delay | Detected | Decoded")
    print("--------------------------")


    for delay_value in args.delays:

        detected, decoded = run_test(
            args,
            delay_value
        )

        results.append([
            delay_value,
            args.sync_length,
            detected,
            decoded
        ])

        print(
            f"{delay_value:5d} | "
            f"{detected:8d} | "
            f"{decoded:7d}"
        )


    # ========================================================
    # Save results
    # ========================================================

    with open(
        args.csv,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "delay",
            "sync_length",
            "detected_sync_short",
            "decoded_frames"
        ])

        writer.writerows(results)


    print()
    print(
        "Results saved to:",
        args.csv
    )


if __name__ == "__main__":
    main()
