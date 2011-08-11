#=============enthought library imports=======================
from pyface.timer.api import do_after as do_after_timer

#=============standard library imports ========================
from numpy import hstack, Inf
#=============local library imports  ==========================
from src.graph.editors.stream_plot_editor import StreamPlotEditor
from stacked_graph import StackedGraph
from graph import Graph

MAX_LIMIT = int(-1e7)

from src.helpers.datetime_tools import current_time_generator as time_generator


class StreamGraph(Graph):
    '''
    '''
    plot_editor_klass = StreamPlotEditor
    global_time_generator = None


    cur_min = Inf
    cur_max = -Inf
    def clear(self):
        self.scan_delays = []
        self.time_generators = []
        self.data_limits = []
        self.track_amounts = []
        self.update_x_limits = []
        super(StreamGraph, self).clear()

    def new_plot(self, **kw):
        '''
        '''
        sd = kw['scan_delay'] if 'scan_deley' in kw else 0.5
        dl = kw['data_limit'] if 'data_limit' in kw else 500
        tl = kw['track_amount'] if 'track_amount' in kw else 0
        self.scan_delays.append(sd)
        self.data_limits.append(dl)
        self.track_amounts.append(tl)

        self.update_x_limits.append(True)

        args = super(StreamGraph, self).new_plot(**kw)
        self.set_x_limits(min = 0, max = dl, plotid = len(self.plots) - 1)

        return args

    def auto_update(self, au, plotid = 0):
        '''
        '''
#        self.trim_data[plotid] = au
        self.update_x_limits[plotid] = au

    def set_scan_delay(self, v, plotid = 0):
        self.scan_delays[plotid] = v

    def set_time_zero(self, plotid = 0):

        tg = time_generator(self.scan_delays[plotid])
        try:
            self.time_generators[plotid] = tg
        except IndexError:
            self.time_generators.append(tg)



    def record_multiple(self, ys, plotid = 0, **kw):

        tg = self.global_time_generator
        if tg is None:
#            tg = time_generator(self.scan_delays[plotid])
            tg = time_generator(self.scan_delays[plotid])
            self.global_time_generator = tg

        x = tg.next()
        for i, yi in enumerate(ys):
            self.record(yi, x = x, series = i, update_x = False, **kw)

        ma = max(ys)
        mi = min(ys)
        if ma < self.cur_max:
            self.cur_max = -Inf
        if mi > self.cur_min:
            self.cur_min = Inf

        dl = self.data_limits[plotid]
#
        if x >= ((dl - 1) * self.scan_delays[plotid]):
            self.set_x_limits(max = x + 1,
                          min = x - (dl - 1) * self.scan_delays[plotid],
                          plotid = plotid,
                          )
        return x

    def record(self, y, x = None, series = 0, plotid = 0, update_x = True, do_after = None):
        xn, yn = self.series[plotid][series]

        plot = self.plots[plotid]

        xd = plot.data.get_data(xn)
        yd = plot.data.get_data(yn)

        if x is None:
            try:
                tg = self.time_generators[plotid]


            except:
#                tg = time_generator(self.scan_delays[plotid])
                tg = time_generator(self.scan_delays[plotid])
                self.time_generators.append(tg)

            nx = tg.next()
        else:
            nx = x


        ny = float(y)

        rx = self.raw_x[plotid][series]
        ry = self.raw_y[plotid][series]

        self.raw_x[plotid][series] = hstack((rx[MAX_LIMIT:], [nx]))
        self.raw_y[plotid][series] = hstack((ry[MAX_LIMIT:], [ny]))

        dl = self.data_limits[plotid]
        lim = int(-(dl + 2) / (self.scan_delays[plotid]))

        new_xd = hstack((xd[lim:], [nx]))
        new_yd = hstack((yd[lim:], [ny]))

        def _record_():
            plot.data.set_data(xn, new_xd)
            plot.data.set_data(yn, new_yd)

            if update_x:
                ma = new_xd[-1]
                mi = new_xd[0]
                if ma >= ((dl - 1) * self.scan_delays[plotid]) - 1:
                    #print self.plot_windows[plotid], self.plot_windows[plotid] - dl * self.scan_delays[plotid]
                    self.set_x_limits(max = ma,
                                  min = mi,
                                  plotid = plotid,
                                  pad = 1
                                  )
#                    self.plot_windows[plotid] += self.scan_delays[plotid]

            pad = True
            if pad:
                ma = max(new_yd)
                mi = min(new_yd)
                if ma > self.cur_max:
                    self.cur_max = ma
                if mi < self.cur_min:
                    self.cur_min = mi

                self.set_y_limits(max = self.cur_max ,
                              min = self.cur_min,
                              plotid = plotid)

        if do_after:
            do_after_timer(do_after, _record_)
        else:
            _record_()

        return nx
class StreamStackedGraph(StreamGraph, StackedGraph):
    pass
#============= EOF ====================================
#    def set_x_limits(self, *args, **kw):
#        '''
#            @type *args: C{str}
#            @param *args:
#
#            @type **kw: C{str}
#            @param **kw:
#        '''
#
#        super(StreamGraph, self).set_x_limits(*args, **kw)
##        pid = kw['plotid']
##        args = self._get_limits('index', pid)
#
##        if args is not None:
##
##            self.data_limits[pid] = max(args[0], args[1])


#    def record(self, val, series = 0, plotid = 0):
#        '''
#            @type val: C{str}
#            @param val:
#
#            @type series: C{str}
#            @param series:
#
#            @type plotid: C{str}
#            @param plotid:
#
#            @type block_write: C{str}
#            @param block_write:
#        '''
#
#        xn, yn = self.series[plotid][series]
#
#        plot = self.plots[plotid]
#
#        xd = plot.data.get_data(xn)
#        yd = plot.data.get_data(yn)
#
#        if isinstance(val, tuple) or isinstance(val, list):
#            x = float(val[0])
#            y = float(val[1])
#        else:
#            y = val
#            if y is not None:
#                y = float(y)
#
#            x = 0
#            try:
#                tg = self.time_generators[plotid]
#
#            except:
#                tg = time_generator()
#                self.time_generators.append(tg)
#
#            x = tg.next()
#
#        dl = self.data_limits[plotid]
#
#        lim = 0
#        if self.trim_data[plotid]:
#            lim = int(-dl / (self.scan_delays[plotid])) + 1
#
#        if y is not None:
#            new_xd = hstack((xd[lim:], [x]))
#            new_yd = hstack((yd[lim:], [y]))
#        else:
#            if x > dl:
#                lim = 1
#
#            new_xd = xd[lim:]
#            new_yd = yd[lim:]
#
#
#        plot.data.set_data(xn, new_xd)
#        plot.data.set_data(yn, new_yd)
#
#        if x > dl and self.update_x_limits[plotid]:
#            self.set_x_limits(track = dl, plotid = plotid)
#            self.update_x_limits[plotid] = False
