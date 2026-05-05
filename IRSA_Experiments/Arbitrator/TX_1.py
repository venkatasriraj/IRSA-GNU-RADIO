#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: 1TX
# Author: venka
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import blocks
from gnuradio import channels
from gnuradio.filter import firdes
from gnuradio import digital
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import zeromq
import TX_1_epy_block_1 as epy_block_1  # embedded python block
import TX_1_epy_block_2 as epy_block_2  # embedded python block
import TX_1_epy_block_3_0 as epy_block_3_0  # embedded python block
import TX_1_epy_block_7 as epy_block_7  # embedded python block
import sip
import threading



class TX_1(gr.top_block, Qt.QWidget):

    def __init__(self, addr1='tcp://127.0.0.1:49212', addr2='tcp://127.0.0.1:49213', iq1_1='iq_samplesTX1.csv', iq1_2='iq_badd1.csv', iq2_1='iq_samplesTX2.csv', iq2_2='iq_badd2.csv', iq_add='iq_Aadd.csv', log_file1='data_tx1.csv', log_file2='data_tx2.csv'):
        gr.top_block.__init__(self, "1TX", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("1TX")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "TX_1")

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
        self.addr1 = addr1
        self.addr2 = addr2
        self.iq1_1 = iq1_1
        self.iq1_2 = iq1_2
        self.iq2_1 = iq2_1
        self.iq2_2 = iq2_2
        self.iq_add = iq_add
        self.log_file1 = log_file1
        self.log_file2 = log_file2

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.samp_rate = samp_rate = 32000
        self.excess_bw = excess_bw = 0.35
        self.bw = bw = (1+excess_bw)*(samp_rate//sps)
        self.access_key = access_key = '1010101010101010101010101010101011100001010110101110100010010011'
        self.usrp_rate = usrp_rate = 32e3
        self.user_id2 = user_id2 = 2
        self.user_id1 = user_id1 = 1
        self.time_offset = time_offset = 1.000
        self.taps = taps = [1.0 + 0.0j, ]
        self.samp_rate_0 = samp_rate_0 = 768000
        self.rs_ratio = rs_ratio = 1.0
        self.noise_volt = noise_volt = 0.0
        self.low_pass_filter_taps = low_pass_filter_taps = firdes.low_pass(1.0, samp_rate, (bw//2)+5e3, 10e3, window.WIN_HAMMING, 6.76)
        self.hdr_format = hdr_format = digital.header_format_default(access_key, 0)
        self.freq_offset = freq_offset = 0
        self.bpsk = bpsk = digital.constellation_bpsk().base()
        self.bpsk.set_npwr(1.0)

        ##################################################
        # Blocks
        ##################################################

        self._time_offset_range = qtgui.Range(0.999, 1.001, 0.0001, 1.000, 200)
        self._time_offset_win = qtgui.RangeWidget(self._time_offset_range, self.set_time_offset, "Timing Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._time_offset_win)
        self._noise_volt_range = qtgui.Range(0, 1, 0.01, 0.0, 200)
        self._noise_volt_win = qtgui.RangeWidget(self._noise_volt_range, self.set_noise_volt, "Noise Voltage", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._noise_volt_win)
        self._freq_offset_range = qtgui.Range(-0.1, 0.1, 0.001, 0, 200)
        self._freq_offset_win = qtgui.RangeWidget(self._freq_offset_range, self.set_freq_offset, "Frequency Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_offset_win)
        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:49203', 100, False, (-1), '', False)
        self.zeromq_pub_sink_0 = zeromq.pub_sink(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:49201', 100, False, (-1), '', True, False)
        # Create the options list
        self._samp_rate_0_options = [768000, 576000]
        # Create the labels list
        self._samp_rate_0_labels = ['768000', '576000']
        # Create the combo box
        self._samp_rate_0_tool_bar = Qt.QToolBar(self)
        self._samp_rate_0_tool_bar.addWidget(Qt.QLabel("Sample rate" + ": "))
        self._samp_rate_0_combo_box = Qt.QComboBox()
        self._samp_rate_0_tool_bar.addWidget(self._samp_rate_0_combo_box)
        for _label in self._samp_rate_0_labels: self._samp_rate_0_combo_box.addItem(_label)
        self._samp_rate_0_callback = lambda i: Qt.QMetaObject.invokeMethod(self._samp_rate_0_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._samp_rate_0_options.index(i)))
        self._samp_rate_0_callback(self.samp_rate_0)
        self._samp_rate_0_combo_box.currentIndexChanged.connect(
            lambda i: self.set_samp_rate_0(self._samp_rate_0_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._samp_rate_0_tool_bar)
        self.qtgui_time_sink_x_1 = qtgui.time_sink_c(
            1024, #size
            samp_rate, #samp_rate
            'iq samples post pdu', #name
            2, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_1.set_update_time(0.10)
        self.qtgui_time_sink_x_1.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_1.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_1.enable_tags(True)
        self.qtgui_time_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, 'packet_len')
        self.qtgui_time_sink_x_1.enable_autoscale(False)
        self.qtgui_time_sink_x_1.enable_grid(False)
        self.qtgui_time_sink_x_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_1.enable_control_panel(False)
        self.qtgui_time_sink_x_1.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
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


        for i in range(4):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_1.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_1.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_1_win = sip.wrapinstance(self.qtgui_time_sink_x_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_1_win)
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
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.complex_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.mmse_resampler_xx_0_0_0 = filter.mmse_resampler_cc(0, (1.0  / ( ( usrp_rate / samp_rate ) * rs_ratio )))
        self.fft_filter_xxx_0_0_0 = filter.fft_filter_ccc(1, low_pass_filter_taps, 1)
        self.fft_filter_xxx_0_0_0.declare_sample_delay(0)
        self.epy_block_7 = epy_block_7.blk()
        self.epy_block_3_0 = epy_block_3_0.blk(user_id=user_id1, samp_rate=usrp_rate)
        self.epy_block_2 = epy_block_2.Random_Packet_Generator(mean_interval=1.6, packet_size=20, user_id=1, log_file=log_file1, total_packets=3, initial_delay=3)
        self.epy_block_1 = epy_block_1.iq_logger_with_timestamp(iq_csv_filename=iq1_1)
        self.digital_protocol_formatter_bb_0 = digital.protocol_formatter_bb(hdr_format, "packet_len")
        self.digital_crc32_bb_0 = digital.crc32_bb(False, "packet_len", True)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=bpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.channels_channel_model_0 = channels.channel_model(
            noise_voltage=noise_volt,
            frequency_offset=freq_offset,
            epsilon=time_offset,
            taps=taps,
            noise_seed=0,
            block_tags=True)
        self.blocks_uchar_to_float_0_0_0_0 = blocks.uchar_to_float()
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, 'packet_len', 0)
        self.blocks_tagged_stream_multiply_length_0 = blocks.tagged_stream_multiply_length(gr.sizeof_gr_complex*1, 'packet_len', (sps*8))
        self.blocks_tag_debug_0 = blocks.tag_debug(gr.sizeof_gr_complex*1, 'tx1', "")
        self.blocks_tag_debug_0.set_display(True)
        self.blocks_repack_bits_bb_0_0 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_2, 'pdu_out'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.epy_block_7, 'burst_in'))
        self.connect((self.blocks_repack_bits_bb_0_0, 0), (self.blocks_uchar_to_float_0_0_0_0, 0))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.blocks_repack_bits_bb_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_uchar_to_float_0_0_0_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.zeromq_pub_sink_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.epy_block_1, 0))
        self.connect((self.digital_crc32_bb_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.digital_crc32_bb_0, 0), (self.digital_protocol_formatter_bb_0, 0))
        self.connect((self.digital_protocol_formatter_bb_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.epy_block_1, 0), (self.fft_filter_xxx_0_0_0, 0))
        self.connect((self.epy_block_3_0, 0), (self.blocks_tagged_stream_multiply_length_0, 0))
        self.connect((self.epy_block_3_0, 0), (self.qtgui_time_sink_x_1, 1))
        self.connect((self.epy_block_7, 0), (self.blocks_tag_debug_0, 0))
        self.connect((self.epy_block_7, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.epy_block_7, 0), (self.qtgui_time_sink_x_1, 0))
        self.connect((self.fft_filter_xxx_0_0_0, 0), (self.mmse_resampler_xx_0_0_0, 0))
        self.connect((self.mmse_resampler_xx_0_0_0, 0), (self.epy_block_3_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.digital_crc32_bb_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.channels_channel_model_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "TX_1")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_addr1(self):
        return self.addr1

    def set_addr1(self, addr1):
        self.addr1 = addr1

    def get_addr2(self):
        return self.addr2

    def set_addr2(self, addr2):
        self.addr2 = addr2

    def get_iq1_1(self):
        return self.iq1_1

    def set_iq1_1(self, iq1_1):
        self.iq1_1 = iq1_1
        self.epy_block_1.iq_csv_filename = self.iq1_1

    def get_iq1_2(self):
        return self.iq1_2

    def set_iq1_2(self, iq1_2):
        self.iq1_2 = iq1_2

    def get_iq2_1(self):
        return self.iq2_1

    def set_iq2_1(self, iq2_1):
        self.iq2_1 = iq2_1

    def get_iq2_2(self):
        return self.iq2_2

    def set_iq2_2(self, iq2_2):
        self.iq2_2 = iq2_2

    def get_iq_add(self):
        return self.iq_add

    def set_iq_add(self, iq_add):
        self.iq_add = iq_add

    def get_log_file1(self):
        return self.log_file1

    def set_log_file1(self, log_file1):
        self.log_file1 = log_file1
        self.epy_block_2.log_file = self.log_file1

    def get_log_file2(self):
        return self.log_file2

    def set_log_file2(self, log_file2):
        self.log_file2 = log_file2

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_bw((1+self.excess_bw)*(self.samp_rate//self.sps))
        self.blocks_tagged_stream_multiply_length_0.set_scalar((self.sps*8))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_bw((1+self.excess_bw)*(self.samp_rate//self.sps))
        self.set_low_pass_filter_taps(firdes.low_pass(1.0, self.samp_rate, (self.bw//2)+5e3, 10e3, window.WIN_HAMMING, 6.76))
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.mmse_resampler_xx_0_0_0.set_resamp_ratio((1.0  / ( ( self.usrp_rate / self.samp_rate ) * self.rs_ratio )))
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_1.set_samp_rate(self.samp_rate)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw
        self.set_bw((1+self.excess_bw)*(self.samp_rate//self.sps))

    def get_bw(self):
        return self.bw

    def set_bw(self, bw):
        self.bw = bw
        self.set_low_pass_filter_taps(firdes.low_pass(1.0, self.samp_rate, (self.bw//2)+5e3, 10e3, window.WIN_HAMMING, 6.76))

    def get_access_key(self):
        return self.access_key

    def set_access_key(self, access_key):
        self.access_key = access_key
        self.set_hdr_format(digital.header_format_default(self.access_key, 0))

    def get_usrp_rate(self):
        return self.usrp_rate

    def set_usrp_rate(self, usrp_rate):
        self.usrp_rate = usrp_rate
        self.epy_block_3_0.samp_rate = self.usrp_rate
        self.mmse_resampler_xx_0_0_0.set_resamp_ratio((1.0  / ( ( self.usrp_rate / self.samp_rate ) * self.rs_ratio )))

    def get_user_id2(self):
        return self.user_id2

    def set_user_id2(self, user_id2):
        self.user_id2 = user_id2

    def get_user_id1(self):
        return self.user_id1

    def set_user_id1(self, user_id1):
        self.user_id1 = user_id1

    def get_time_offset(self):
        return self.time_offset

    def set_time_offset(self, time_offset):
        self.time_offset = time_offset
        self.channels_channel_model_0.set_timing_offset(self.time_offset)

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps
        self.channels_channel_model_0.set_taps(self.taps)

    def get_samp_rate_0(self):
        return self.samp_rate_0

    def set_samp_rate_0(self, samp_rate_0):
        self.samp_rate_0 = samp_rate_0
        self._samp_rate_0_callback(self.samp_rate_0)

    def get_rs_ratio(self):
        return self.rs_ratio

    def set_rs_ratio(self, rs_ratio):
        self.rs_ratio = rs_ratio
        self.mmse_resampler_xx_0_0_0.set_resamp_ratio((1.0  / ( ( self.usrp_rate / self.samp_rate ) * self.rs_ratio )))

    def get_noise_volt(self):
        return self.noise_volt

    def set_noise_volt(self, noise_volt):
        self.noise_volt = noise_volt
        self.channels_channel_model_0.set_noise_voltage(self.noise_volt)

    def get_low_pass_filter_taps(self):
        return self.low_pass_filter_taps

    def set_low_pass_filter_taps(self, low_pass_filter_taps):
        self.low_pass_filter_taps = low_pass_filter_taps
        self.fft_filter_xxx_0_0_0.set_taps(self.low_pass_filter_taps)

    def get_hdr_format(self):
        return self.hdr_format

    def set_hdr_format(self, hdr_format):
        self.hdr_format = hdr_format
        self.digital_protocol_formatter_bb_0.set_header_format(self.hdr_format)

    def get_freq_offset(self):
        return self.freq_offset

    def set_freq_offset(self, freq_offset):
        self.freq_offset = freq_offset
        self.channels_channel_model_0.set_frequency_offset(self.freq_offset)

    def get_bpsk(self):
        return self.bpsk

    def set_bpsk(self, bpsk):
        self.bpsk = bpsk



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--addr1", dest="addr1", type=str, default='tcp://127.0.0.1:49212',
        help="Set tcp [default=%(default)r]")
    parser.add_argument(
        "--addr2", dest="addr2", type=str, default='tcp://127.0.0.1:49213',
        help="Set tcp [default=%(default)r]")
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
    return parser


def main(top_block_cls=TX_1, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(addr1=options.addr1, addr2=options.addr2, iq1_1=options.iq1_1, iq1_2=options.iq1_2, iq2_1=options.iq2_1, iq2_2=options.iq2_2, iq_add=options.iq_add, log_file1=options.log_file1, log_file2=options.log_file2)

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
