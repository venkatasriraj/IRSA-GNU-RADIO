#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: pkt_xmt
# Author: Barry Duggan
# Description: packet transmit
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, blocks
import pmt
from gnuradio import gr, pdu
from gnuradio import zeromq
import pkt_xmt_epy_block_1 as epy_block_1  # embedded python block
import pkt_xmt_epy_block_1_0_0 as epy_block_1_0_0  # embedded python block
import pkt_xmt_epy_block_1_0_0_0 as epy_block_1_0_0_0  # embedded python block
import pkt_xmt_epy_block_1_0_0_1 as epy_block_1_0_0_1  # embedded python block
import pkt_xmt_epy_block_1_1 as epy_block_1_1  # embedded python block
import pkt_xmt_epy_block_2 as epy_block_2  # embedded python block
import pkt_xmt_epy_block_2_0 as epy_block_2_0  # embedded python block
import sip
import threading



class pkt_xmt(gr.top_block, Qt.QWidget):

    def __init__(self, InFile='file.txt', iq1_1='iq_samplesTX1.csv', iq1_2='iq_badd1.csv', iq2_1='iq_samplesTX2.csv', iq2_2='iq_badd2.csv', iq_add='iq_Aadd.csv', log_file1='data_tx1.csv', log_file2='data_tx2.csv', timestamp1_1='timestamps1_1.txt', timestamp1_2='timestampsTx1_2.txt', timestamp2_1='timestamps2_1.txt', timestamp2_2='timestampsTx2_2.txt', timestamp_add='timestamp_add.txt'):
        gr.top_block.__init__(self, "pkt_xmt", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("pkt_xmt")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pkt_xmt")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.InFile = InFile
        self.iq1_1 = iq1_1
        self.iq1_2 = iq1_2
        self.iq2_1 = iq2_1
        self.iq2_2 = iq2_2
        self.iq_add = iq_add
        self.log_file1 = log_file1
        self.log_file2 = log_file2
        self.timestamp1_1 = timestamp1_1
        self.timestamp1_2 = timestamp1_2
        self.timestamp2_1 = timestamp2_1
        self.timestamp2_2 = timestamp2_2
        self.timestamp_add = timestamp_add

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 48000
        self.access_key = access_key = '11100001010110101110100010010011'
        self.usrp_rate = usrp_rate = 768000
        self.user_id2 = user_id2 = 2
        self.user_id1 = user_id1 = 1
        self.sps = sps = 4
        self.rs_ratio = rs_ratio = 1.040
        self.low_pass_filter_taps = low_pass_filter_taps = firdes.low_pass(1.0, samp_rate, 20000, 2000, window.WIN_HAMMING, 6.76)
        self.hdr_format = hdr_format = digital.header_format_default(access_key, 0)
        self.excess_bw = excess_bw = 0.35
        self.bpsk = bpsk = digital.constellation_bpsk().base()
        self.bpsk.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        self.zeromq_pub_sink_0 = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:49203', 100, False, (-1), '', True, True)
        self.qtgui_time_sink_x_0_0 = qtgui.time_sink_f(
            256, #size
            samp_rate, #samp_rate
            'Transmit data 2', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0.set_y_axis(-0.1, 1.1)

        self.qtgui_time_sink_x_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.1, 0.0, 0, "packet_len")
        self.qtgui_time_sink_x_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0.enable_stem_plot(False)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_win, 2, 0, 1, 3)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            256, #size
            samp_rate, #samp_rate
            'Transmit data 1', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-0.1, 1.1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.1, 0.0, 0, "packet_len")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_win, 1, 0, 1, 3)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 3):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.pdu_pdu_to_tagged_stream_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.mmse_resampler_xx_0_0 = filter.mmse_resampler_cc(0, (1.0/((usrp_rate/samp_rate)*rs_ratio)))
        self.mmse_resampler_xx_0 = filter.mmse_resampler_cc(0, (1.0/((usrp_rate/samp_rate)*rs_ratio)))
        self.fft_filter_xxx_0_0_0_0 = filter.fft_filter_ccc(1, low_pass_filter_taps, 1)
        self.fft_filter_xxx_0_0_0_0.declare_sample_delay(0)
        self.fft_filter_xxx_0_0_0 = filter.fft_filter_ccc(1, low_pass_filter_taps, 1)
        self.fft_filter_xxx_0_0_0.declare_sample_delay(0)
        self.epy_block_2_0 = epy_block_2_0.Random_Packet_Generator(mean_interval=29, packet_size=52, user_id=2, log_file=log_file2)
        self.epy_block_2 = epy_block_2.Random_Packet_Generator(mean_interval=10, packet_size=52, user_id=1, log_file=log_file1)
        self.epy_block_1_1 = epy_block_1_1.iq_logger_with_timestamp(iq_csv_filename=iq2_1)
        self.epy_block_1_0_0_1 = epy_block_1_0_0_1.iq_logger_with_timestamp(iq_csv_filename=iq_add)
        self.epy_block_1_0_0_0 = epy_block_1_0_0_0.iq_logger_with_timestamp(iq_csv_filename=iq2_2)
        self.epy_block_1_0_0 = epy_block_1_0_0.iq_logger_with_timestamp(iq_csv_filename=iq1_2)
        self.epy_block_1 = epy_block_1.iq_logger_with_timestamp(iq_csv_filename=iq1_1)
        self.digital_protocol_formatter_bb_0_0 = digital.protocol_formatter_bb(hdr_format, "packet_len")
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(hdr_format, "packet_len")
        self.digital_crc32_bb_0_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_crc32_bb_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_constellation_modulator_0_0 = digital.generic_mod(
            constellation=bpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=bpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.blocks_uchar_to_float_0_0_0_0_0 = blocks.uchar_to_float()
        self.blocks_uchar_to_float_0_0_0_0 = blocks.uchar_to_float()
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, usrp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * usrp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_mux_0_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_repack_bits_bb_0_0_0 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_0_0 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_file_meta_sink_0_0 = blocks.file_meta_sink(gr.sizeof_gr_complex*1, 'iq_samples.dat', samp_rate, 1, blocks.GR_FILE_FLOAT, True, 1000000, pmt.make_dict(), True)
        self.blocks_file_meta_sink_0_0.set_unbuffered(True)
        self.blocks_add_xx_0 = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_2, 'pdu_out'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.epy_block_2_0, 'pdu_out'), (self.pdu_pdu_to_tagged_stream_0_0, 'pdus'))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_repack_bits_bb_0_0, 0), (self.blocks_uchar_to_float_0_0_0_0, 0))
        self.connect((self.blocks_repack_bits_bb_0_0_0, 0), (self.blocks_uchar_to_float_0_0_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.blocks_repack_bits_bb_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.blocks_repack_bits_bb_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.digital_constellation_modulator_0_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.epy_block_1_0_0_1, 0))
        self.connect((self.blocks_uchar_to_float_0_0_0_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_uchar_to_float_0_0_0_0_0, 0), (self.qtgui_time_sink_x_0_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.epy_block_1, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.blocks_file_meta_sink_0_0, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.epy_block_1_1, 0))
        self.connect((self.digital_crc32_bb_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.digital_crc32_bb_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 1))
        self.connect((self.digital_crc32_bb_0_0, 0), (self.digital_protocol_formatter_bb_0_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 0))
        self.connect((self.epy_block_1, 0), (self.fft_filter_xxx_0_0_0, 0))
        self.connect((self.epy_block_1_0_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.epy_block_1_0_0_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.epy_block_1_0_0_1, 0), (self.zeromq_pub_sink_0, 0))
        self.connect((self.epy_block_1_1, 0), (self.fft_filter_xxx_0_0_0_0, 0))
        self.connect((self.fft_filter_xxx_0_0_0, 0), (self.mmse_resampler_xx_0, 0))
        self.connect((self.fft_filter_xxx_0_0_0_0, 0), (self.mmse_resampler_xx_0_0, 0))
        self.connect((self.mmse_resampler_xx_0, 0), (self.epy_block_1_0_0, 0))
        self.connect((self.mmse_resampler_xx_0_0, 0), (self.epy_block_1_0_0_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.digital_crc32_bb_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0, 0), (self.digital_crc32_bb_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "pkt_xmt")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_InFile(self):
        return self.InFile

    def set_InFile(self, InFile):
        self.InFile = InFile

    def get_iq1_1(self):
        return self.iq1_1

    def set_iq1_1(self, iq1_1):
        self.iq1_1 = iq1_1
        self.epy_block_1.iq_csv_filename = self.iq1_1

    def get_iq1_2(self):
        return self.iq1_2

    def set_iq1_2(self, iq1_2):
        self.iq1_2 = iq1_2
        self.epy_block_1_0_0.iq_csv_filename = self.iq1_2

    def get_iq2_1(self):
        return self.iq2_1

    def set_iq2_1(self, iq2_1):
        self.iq2_1 = iq2_1
        self.epy_block_1_1.iq_csv_filename = self.iq2_1

    def get_iq2_2(self):
        return self.iq2_2

    def set_iq2_2(self, iq2_2):
        self.iq2_2 = iq2_2
        self.epy_block_1_0_0_0.iq_csv_filename = self.iq2_2

    def get_iq_add(self):
        return self.iq_add

    def set_iq_add(self, iq_add):
        self.iq_add = iq_add
        self.epy_block_1_0_0_1.iq_csv_filename = self.iq_add

    def get_log_file1(self):
        return self.log_file1

    def set_log_file1(self, log_file1):
        self.log_file1 = log_file1
        self.epy_block_2.log_file = self.log_file1

    def get_log_file2(self):
        return self.log_file2

    def set_log_file2(self, log_file2):
        self.log_file2 = log_file2
        self.epy_block_2_0.log_file = self.log_file2

    def get_timestamp1_1(self):
        return self.timestamp1_1

    def set_timestamp1_1(self, timestamp1_1):
        self.timestamp1_1 = timestamp1_1

    def get_timestamp1_2(self):
        return self.timestamp1_2

    def set_timestamp1_2(self, timestamp1_2):
        self.timestamp1_2 = timestamp1_2

    def get_timestamp2_1(self):
        return self.timestamp2_1

    def set_timestamp2_1(self, timestamp2_1):
        self.timestamp2_1 = timestamp2_1

    def get_timestamp2_2(self):
        return self.timestamp2_2

    def set_timestamp2_2(self, timestamp2_2):
        self.timestamp2_2 = timestamp2_2

    def get_timestamp_add(self):
        return self.timestamp_add

    def set_timestamp_add(self, timestamp_add):
        self.timestamp_add = timestamp_add

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_low_pass_filter_taps(firdes.low_pass(1.0, self.samp_rate, 20000, 2000, window.WIN_HAMMING, 6.76))
        self.mmse_resampler_xx_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))
        self.mmse_resampler_xx_0_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_0_0.set_samp_rate(self.samp_rate)

    def get_access_key(self):
        return self.access_key

    def set_access_key(self, access_key):
        self.access_key = access_key
        self.set_hdr_format(digital.header_format_default(self.access_key, 0))

    def get_usrp_rate(self):
        return self.usrp_rate

    def set_usrp_rate(self, usrp_rate):
        self.usrp_rate = usrp_rate
        self.blocks_throttle2_0.set_sample_rate(self.usrp_rate)
        self.mmse_resampler_xx_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))
        self.mmse_resampler_xx_0_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))

    def get_user_id2(self):
        return self.user_id2

    def set_user_id2(self, user_id2):
        self.user_id2 = user_id2

    def get_user_id1(self):
        return self.user_id1

    def set_user_id1(self, user_id1):
        self.user_id1 = user_id1

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps

    def get_rs_ratio(self):
        return self.rs_ratio

    def set_rs_ratio(self, rs_ratio):
        self.rs_ratio = rs_ratio
        self.mmse_resampler_xx_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))
        self.mmse_resampler_xx_0_0.set_resamp_ratio((1.0/((self.usrp_rate/self.samp_rate)*self.rs_ratio)))

    def get_low_pass_filter_taps(self):
        return self.low_pass_filter_taps

    def set_low_pass_filter_taps(self, low_pass_filter_taps):
        self.low_pass_filter_taps = low_pass_filter_taps
        self.fft_filter_xxx_0_0_0.set_taps(self.low_pass_filter_taps)
        self.fft_filter_xxx_0_0_0_0.set_taps(self.low_pass_filter_taps)

    def get_hdr_format(self):
        return self.hdr_format

    def set_hdr_format(self, hdr_format):
        self.hdr_format = hdr_format
        self.digital_protocol_formatter_bb_0.set_header_format(self.hdr_format)
        self.digital_protocol_formatter_bb_0_0.set_header_format(self.hdr_format)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw

    def get_bpsk(self):
        return self.bpsk

    def set_bpsk(self, bpsk):
        self.bpsk = bpsk



def argument_parser():
    description = 'packet transmit'
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--InFile", dest="InFile", type=str, default='file.txt',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--iq1-1", dest="iq1_1", type=str, default='iq_samplesTX1.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--iq1-2", dest="iq1_2", type=str, default='iq_badd1.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--iq2-1", dest="iq2_1", type=str, default='iq_samplesTX2.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--iq2-2", dest="iq2_2", type=str, default='iq_badd2.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--iq-add", dest="iq_add", type=str, default='iq_Aadd.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--log-file1", dest="log_file1", type=str, default='data_tx1.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--log-file2", dest="log_file2", type=str, default='data_tx2.csv',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--timestamp1-1", dest="timestamp1_1", type=str, default='timestamps1_1.txt',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--timestamp1-2", dest="timestamp1_2", type=str, default='timestampsTx1_2.txt',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--timestamp2-1", dest="timestamp2_1", type=str, default='timestamps2_1.txt',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--timestamp2-2", dest="timestamp2_2", type=str, default='timestampsTx2_2.txt',
        help="Set File Name [default=%(default)r]")
    parser.add_argument(
        "--timestamp-add", dest="timestamp_add", type=str, default='timestamp_add.txt',
        help="Set File Name [default=%(default)r]")
    return parser


def main(top_block_cls=pkt_xmt, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(InFile=options.InFile, iq1_1=options.iq1_1, iq1_2=options.iq1_2, iq2_1=options.iq2_1, iq2_2=options.iq2_2, iq_add=options.iq_add, log_file1=options.log_file1, log_file2=options.log_file2, timestamp1_1=options.timestamp1_1, timestamp1_2=options.timestamp1_2, timestamp2_1=options.timestamp2_1, timestamp2_2=options.timestamp2_2, timestamp_add=options.timestamp_add)

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
