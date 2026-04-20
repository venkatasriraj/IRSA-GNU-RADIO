#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: bpsk_stage6_ver2
# Author: Barry Duggan, updated by Gary Schafer
# Description: Using Diff Enc / Replaced Polyphase Clock Sync with Symbol Sync
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
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
from gnuradio import soapy
import sip
import threading



class bpsk_stage6_ver2(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "bpsk_stage6_ver2", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("bpsk_stage6_ver2")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "bpsk_stage6_ver2")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 10
        self.samp_rate = samp_rate = 2e6
        self.nfilts = nfilts = 32
        self.excess_bw = excess_bw = 0.35
        self.bpsk = bpsk = digital.constellation_bpsk().base()
        self.bpsk.set_npwr(1.0)
        self.tuning = tuning = 915e6
        self.timing_loop_bw = timing_loop_bw = 45e-3
        self.taps = taps = [1.0 + 0.0j, ]
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1, samp_rate, samp_rate/float(sps), excess_bw, 11*nfilts)
        self.phase_bw = phase_bw = 62.8e-3
        self.loop_order = loop_order = 2
        self.fc = fc = 99.5e6
        self.cmaEqualizer = cmaEqualizer = digital.adaptive_algorithm_cma( bpsk, .0001, 4).base()
        self.center_freq = center_freq = 915e6
        self.bw = bw = (samp_rate//sps)*(1+excess_bw)

        ##################################################
        # Blocks
        ##################################################

        self._tuning_range = qtgui.Range(912e6, 918e6, 0.5e6, 915e6, 200)
        self._tuning_win = qtgui.RangeWidget(self._tuning_range, self.set_tuning, "'tuning'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tuning_win)
        self._timing_loop_bw_range = qtgui.Range(40e-3, 100e-3, 0.1e-3, 45e-3, 200)
        self._timing_loop_bw_win = qtgui.RangeWidget(self._timing_loop_bw_range, self.set_timing_loop_bw, "'timing_loop_bw'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._timing_loop_bw_win)
        self._phase_bw_range = qtgui.Range(50e-3, 100e-3, 0.1e-3, 62.8e-3, 200)
        self._phase_bw_win = qtgui.RangeWidget(self._phase_bw_range, self.set_phase_bw, "'phase_bw'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._phase_bw_win)
        self.soapy_hackrf_source_0 = None
        dev = 'driver=hackrf'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_hackrf_source_0 = soapy.source(dev, "fc32", 1, 'driver=hackrf',
                                  stream_args, tune_args, settings)
        self.soapy_hackrf_source_0.set_sample_rate(0, samp_rate)
        self.soapy_hackrf_source_0.set_bandwidth(0, 0)
        self.soapy_hackrf_source_0.set_frequency(0, center_freq)
        self.soapy_hackrf_source_0.set_gain(0, 'AMP', True)
        self.soapy_hackrf_source_0.set_gain(0, 'LNA', min(max(40, 0.0), 40.0))
        self.soapy_hackrf_source_0.set_gain(0, 'VGA', min(max(50, 0.0), 62.0))
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            4096, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "", #name
            3,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 0)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['Received Spectrum', 'Filtered Spectrum', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(3):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_0_win, 12, 0, 10, 20)
        for r in range(12, 22):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 20):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_eye_sink_x_0 = qtgui.eye_sink_c(
            1024, #size
            samp_rate, #samp_rate
            1, #number of inputs
            None
        )
        self.qtgui_eye_sink_x_0.set_update_time(0.10)
        self.qtgui_eye_sink_x_0.set_samp_per_symbol(sps)
        self.qtgui_eye_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_eye_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_eye_sink_x_0.enable_tags(True)
        self.qtgui_eye_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_eye_sink_x_0.enable_autoscale(False)
        self.qtgui_eye_sink_x_0.enable_grid(False)
        self.qtgui_eye_sink_x_0.enable_axis_labels(True)
        self.qtgui_eye_sink_x_0.enable_control_panel(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'blue', 'blue', 'blue', 'blue',
            'blue', 'blue', 'blue', 'blue', 'blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_eye_sink_x_0.set_line_label(i, "Eye [Re{{Data {0}}}]".format(round(i/2)))
                else:
                    self.qtgui_eye_sink_x_0.set_line_label(i, "Eye [Im{{Data {0}}}]".format(round((i-1)/2)))
            else:
                self.qtgui_eye_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_eye_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_eye_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_eye_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_eye_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_eye_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_eye_sink_x_0_win = sip.wrapinstance(self.qtgui_eye_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_eye_sink_x_0_win)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            'Recovered Constellation', #name
            4, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(True)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 2, 2, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 1, 1, 0, 0,
            0, 0, 0, 0, 0]
        markers = [1, -1, -1, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 0.3, 0.3, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(4):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_const_sink_x_0_win, 2, 0, 10, 10)
        for r in range(2, 12):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 10):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_ccc(1, firdes.low_pass(1, samp_rate, 0.5e6, 200e3), (tuning - center_freq), samp_rate)
        self.fft_filter_xxx_0 = filter.fft_filter_ccc(1, rrc_taps, 1)
        self.fft_filter_xxx_0.declare_sample_delay(0)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_MOD_MUELLER_AND_MULLER,
            sps,
            timing_loop_bw,
            1.0,
            1.0,
            1.5,
            1,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_NO_MF,
            128,
            [])
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(phase_bw, loop_order, False)
        self.blocks_vector_source_x_0_0 = blocks.vector_source_c((10j, -10j), True, 1, [])
        self.blocks_vector_source_x_0 = blocks.vector_source_c((10, -10), True, 1, [])


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_vector_source_x_0, 0), (self.qtgui_const_sink_x_0, 1))
        self.connect((self.blocks_vector_source_x_0_0, 0), (self.qtgui_const_sink_x_0, 2))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.qtgui_eye_sink_x_0, 0))
        self.connect((self.fft_filter_xxx_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.fft_filter_xxx_0, 0), (self.qtgui_freq_sink_x_0, 1))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.fft_filter_xxx_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.soapy_hackrf_source_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.soapy_hackrf_source_0, 0), (self.qtgui_const_sink_x_0, 3))
        self.connect((self.soapy_hackrf_source_0, 0), (self.qtgui_freq_sink_x_0, 2))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "bpsk_stage6_ver2")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_bw((self.samp_rate//self.sps)*(1+self.excess_bw))
        self.set_rrc_taps(firdes.root_raised_cosine(1, self.samp_rate, self.samp_rate/float(self.sps), self.excess_bw, 11*self.nfilts))
        self.digital_symbol_sync_xx_0.set_sps(self.sps)
        self.qtgui_eye_sink_x_0.set_samp_per_symbol(self.sps)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_bw((self.samp_rate//self.sps)*(1+self.excess_bw))
        self.set_rrc_taps(firdes.root_raised_cosine(1, self.samp_rate, self.samp_rate/float(self.sps), self.excess_bw, 11*self.nfilts))
        self.freq_xlating_fir_filter_xxx_0.set_taps(firdes.low_pass(1, self.samp_rate, 0.5e6, 200e3))
        self.qtgui_eye_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.soapy_hackrf_source_0.set_sample_rate(0, self.samp_rate)

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(1, self.samp_rate, self.samp_rate/float(self.sps), self.excess_bw, 11*self.nfilts))

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw
        self.set_bw((self.samp_rate//self.sps)*(1+self.excess_bw))
        self.set_rrc_taps(firdes.root_raised_cosine(1, self.samp_rate, self.samp_rate/float(self.sps), self.excess_bw, 11*self.nfilts))

    def get_bpsk(self):
        return self.bpsk

    def set_bpsk(self, bpsk):
        self.bpsk = bpsk

    def get_tuning(self):
        return self.tuning

    def set_tuning(self, tuning):
        self.tuning = tuning
        self.freq_xlating_fir_filter_xxx_0.set_center_freq((self.tuning - self.center_freq))

    def get_timing_loop_bw(self):
        return self.timing_loop_bw

    def set_timing_loop_bw(self, timing_loop_bw):
        self.timing_loop_bw = timing_loop_bw
        self.digital_symbol_sync_xx_0.set_loop_bandwidth(self.timing_loop_bw)

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.fft_filter_xxx_0.set_taps(self.rrc_taps)

    def get_phase_bw(self):
        return self.phase_bw

    def set_phase_bw(self, phase_bw):
        self.phase_bw = phase_bw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.phase_bw)

    def get_loop_order(self):
        return self.loop_order

    def set_loop_order(self, loop_order):
        self.loop_order = loop_order

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc

    def get_cmaEqualizer(self):
        return self.cmaEqualizer

    def set_cmaEqualizer(self, cmaEqualizer):
        self.cmaEqualizer = cmaEqualizer

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.freq_xlating_fir_filter_xxx_0.set_center_freq((self.tuning - self.center_freq))
        self.soapy_hackrf_source_0.set_frequency(0, self.center_freq)

    def get_bw(self):
        return self.bw

    def set_bw(self, bw):
        self.bw = bw




def main(top_block_cls=bpsk_stage6_ver2, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

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
