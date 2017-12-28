"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import CustomFactor, Pipeline, CustomFilter
import numpy as np
from datetime import datetime as DateTime, timedelta as TimeDelta
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters import Q1500US


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every day, 1 hour after market open.
    #schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=1))

    # Record tracking variables at the end of each day.
    #schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())

    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    alpha_long_daily = AlphaLongDaily(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        window_length=1
    )
    alpha_long_weekly = AlphaLongWeekly(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        window_length=9
    )
    # Base universe set to the Q1500US
    #base_universe = Q1500US()

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
    is_setup = alpha_long_weekly & alpha_long_daily
    pipe = Pipeline(
        screen=is_setup,
        columns={
            'yesterday_close': yesterday_close,
            'alpha_long_weekly': alpha_long_weekly
        }
    )
    return pipe


class AlphaLongDaily(CustomFilter):
    def compute(self, today, asset_ids, out, open, high, low, close):
        # Calculates the column-wise standard deviation, ignoring NaNs
        r = (high[0] - low[0]) / 3
        z = high[0] - r
        isSetup = (open[0] > z) & (close[0] > z)
        out[:] = isSetup


class AlphaLongWeekly(CustomFilter):
    def compute(self, today, asset_ids, out, open, high, low, close):
        todayDay = today.weekday()
        # print str(today) + ' ' + str(today.weekday())
        # print '      open: ' + str(open[0][0]) + ' high: ' + str(high[0][0]) + ' low: ' + str(low[0][0]) + ' close: ' + str(close[0][0])
        # print '      open: ' + str(open[1][0]) + ' high: ' + str(high[1][0]) + ' low: ' + str(low[1][0]) + ' close: ' + str(close[1][0])
        # print '      open: ' + str(open[2][0]) + ' high: ' + str(high[2][0]) + ' low: ' + str(low[2][0]) + ' close: ' + str(close[2][0])
        # print '      open: ' + str(open[3][0]) + ' high: ' + str(high[3][0]) + ' low: ' + str(low[3][0]) + ' close: ' + str(close[3][0])

        endWeekIdx = 8 - todayDay
        startWeekIdx = 4 - todayDay

        weekOpen = open[startWeekIdx]
        weekClose = close[endWeekIdx]

        weekHigh = high[startWeekIdx:endWeekIdx, :].max(axis=0)
        weekLow = low[startWeekIdx:endWeekIdx, :].min(axis=0)
      #  print weekLow
        r = (weekHigh - weekLow) / 3
        z = weekHigh - r
        is_setup = (weekOpen > z) & (weekClose > z)
       # print ' daily result ' + str(sid(24).symbol) + ' ' + str(today) + ' ' + str(today.weekday())
        # print 'START WEEK DAY: ' + str(startWeekDay)
        # print '   END WEEK DAY: ' + str(endWeekDay)
        # print '      open: ' + str(open[endWeekIdx][0]) + ' high: ' + str(high[endWeekIdx][0]) + ' low: ' + str(low[endWeekIdx][0]) + ' close: ' + str(close[endWeekIdx][0])
        # print 'open: ' + str(weekOpen[2]) + ' high: ' + str(weekHigh[2]) + ' low: ' + str(weekLow[2]) + ' close: ' + str(weekClose[2])
        out[:] = is_setup


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
    record(numSetupStocks=len(context.output))
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index


def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass


def my_rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    pass


def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass


def handle_data(context, data):
    """
    Called every minute.
    """
   # record(abc=context.output)
    pass
