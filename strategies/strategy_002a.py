"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import CustomFactor, Pipeline, CustomFilter
from quantopian.pipeline.data import Fundamentals
import numpy as np
from quantopian.pipeline.data.builtin import USEquityPricing
from pytz import timezone
import quantopian.optimize as opt
from quantopian.pipeline.filters import StaticSids
from quantopian.pipeline.factors import AverageDollarVolume, SimpleMovingAverage


VOLUME_MIN_AVG = 1000000

BAR_TYPE = {
    'none': 0.0,
    'alpha': 2.0,
    'beta': 4.0,
    'gamma': 8.0,
    'gamma_alpha': 10.0,
    'gamma_beta': 12.0,
    'delta': 16.0,
    'delta_alpha': 18.0,
    'delta_beta': 20.0,
    'theta_plus_final': 32.0,
    'theta_minus_final': 64.0,
    0.0: 'none',
    2.0: 'alpha',
    4.0: 'beta',
    8.0: 'gamma',
    10.0: 'gamma_alpha',
    12.0: 'gamma_beta',
    16.0: 'delta',
    18.0: 'delta_alpha',
    20.0: 'delta_beta',
    32.0: 'theta_plus_final',
    64.0: 'theta_minus_final'
}
ALPHA_DIVISOR = 3
BETA_DIVISOR = 3

USE_STOP_LOSS_EXIT = True

USE_TRAILING_STOP_EXIT = True
TRAILING_STOP_PCT = 0.02

USE_TAKE_PROFIT_EXIT = False
TAKE_PROFIT_EXIT_PCT = 0.01


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # referencing SPY so the 'handle_data' function will be called every minute
    # context.spy = sid(8554)
    context.positions_stop_loss = {}
    context.positions_max_gain = {}
    context.position_logs = {}

    context.daily_stat_history = []
    context.hourly_data = {}
    context.hourly_current_open = {}

    context.outside_months_and_inside_weeks = 0
    context.weekly_break_outs = 0
    context.hourly_break_outs = 0
    context.hourly_inside = 0

    # Record variables at the end of each day.
    schedule_function(record_counts,
                      date_rules.every_day(),
                      time_rules.market_close())

    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """

   # symbol_filter = StaticSids([sid(26758)])
   # exchange = Fundamentals.exchange_id.latest
    # nyse_filter = exchange.eq('NYS')

    # dollar_volume = AverageDollarVolume(window_length=10)
    # high_dollar_volume = dollar_volume.top(TOP_NUM_STOCKS_BY_DOLLAR_VOLUME)
    vol_sma_10 = SimpleMovingAverage(
        inputs=[USEquityPricing.volume], window_length=10)
    vol_filter = vol_sma_10 > VOLUME_MIN_AVG
#    volume_filter = VolumeFilter(
#        inputs=[USEquityPricing.volume],
#        window_length=10
#    )

    # is_setup = volume_filter & alpha_long_weekly & alpha_long_daily
    weekly_high = WeeklyHigh(
        inputs=[USEquityPricing.high],
        mask=vol_filter
    )
    weekly_low = WeeklyLow(
        inputs=[USEquityPricing.low],
        mask=vol_filter
    )
    weekly_gamma_filter = WeeklyGammaFilter(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        mask=vol_filter
    )
    # daily_classifier = DailyClassifier(
    #     inputs=[
    #         USEquityPricing.open,
    #         USEquityPricing.high,
    #         USEquityPricing.low,
    #         USEquityPricing.close
    #     ],
    #     mask=volume_filter

    # )
    monthly_current_open = MonthlyCurrentOpen(
        inputs=[USEquityPricing.open],
        mask=vol_filter
    )
    weekly_current_open = WeeklyCurrentOpen(
        inputs=[USEquityPricing.open],
        mask=vol_filter
    )
    # monthly_low = MonthlyLow(
    #     inputs=[USEquityPricing.low],
    #     mask=volume_filter
    # )
    # monthly_classifier = MonthlyClassifier(
    #     inputs=[
    #         USEquityPricing.open,
    #         USEquityPricing.high,
    #         USEquityPricing.low,
    #         USEquityPricing.close
    #     ],
    #     mask=volume_filter
    # )
    #current_inside_month_classifier = CurrentInsideMonthClassifier(
    #    inputs=[
    #        USEquityPricing.open,
    #        USEquityPricing.high,
    #        USEquityPricing.low,
    #        USEquityPricing.close
    #    ],
    #    mask=vol_filter
    #)

    pipe = Pipeline(
        screen=(weekly_gamma_filter),
        # screen = symbol_filter,
        columns={
            # 'daily_classifier': daily_classifier,
            # 'daily_high': USEquityPricing.high.latest,
            # 'daily_low': USEquityPricing.low.latest,
            'weekly_gamma_filter': weekly_gamma_filter,
            'weekly_high': weekly_high,
            'weekly_low': weekly_low,
            'monthly_current_open': monthly_current_open,
            'weekly_current_open': weekly_current_open
        }
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
    context.current_stock_list = context.output.index.tolist()
    context.hourly_data = {}
   # print(len(context.current_stock_list))

    context.outside_months_and_inside_weeks = len(context.current_stock_list)


def record_counts(context, data):

    longs = len(filter(lambda sec: context.portfolio.positions[sec].amount > 0,  context.portfolio.positions.keys()))
    shorts = len(filter(lambda sec: context.portfolio.positions[sec].amount < 0,  context.portfolio.positions.keys()))
    record(
        longs=longs,
        shorts=shorts
    )

def handle_data(context, data):
    """
    Called every minute.
    """

    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    if exchange_time.hour > 15:
        return ''
    if exchange_time.hour == 15 and exchange_time.minute > 50:
        return ''
   # print exchange_time
    if len(context.current_stock_list) == 0:
        return ''
    open = data.history(context.current_stock_list, "open", 61, "1m", )
    high = data.history(context.current_stock_list, "high", 61, "1m", )
    low = data.history(context.current_stock_list, "low", 61, "1m", )
    close = data.history(context.current_stock_list, "close", 61, "1m", )

    open_orders = get_open_orders()
    open_secs = context.portfolio.positions.keys()
    if open_secs:
        open_sec = data.history(open_secs, "open", 61, "1m", )
        high_sec = data.history(open_secs, "high", 61, "1m", )
        low_sec = data.history(open_secs, "low", 61, "1m", )
        close_sec = data.history(open_secs, "close", 61, "1m", )
        open_daily_sec = data.history(open_secs, "open", 32, "1d", )

    current_prices = data.current(context.current_stock_list, 'price')
    today_open = data.history(context.current_stock_list, "open", 1, "1d")
    # monitor for entries
    for sec in context.current_stock_list:

        if not data.can_trade(sec):
            continue
        # build intraday bars
        construct_hourly_data(sec, exchange_time,
                              context, open, high, low, close)
        
        if sec in open_orders or sec in context.portfolio.positions:
            continue
        pos_count = len(context.portfolio.positions)
        if pos_count == 10:
            continue
            
        monthly_open = context.output['monthly_current_open'][sec]
        if monthly_open == 0:
            monthly_open = today_open[sec][0]
                
        weekly_open = context.output['weekly_current_open'][sec]
        if weekly_open == 0:
            weekly_open = today_open[sec][0]
            
        # Should be trading outside prev months range and be an inside week at this point
        # make sure we have full timeframe continuity i.e. trading above all opens of each timeframe
        if (current_prices[sec] > monthly_open
            and current_prices[sec] > weekly_open
            and current_prices[sec] > today_open[sec][0]
            and current_prices[sec] > context.hourly_current_open[sec]):
            if current_prices[sec] > context.output['weekly_high'][sec]:
                # we've broken out of the week now test the hour
                if sec in context.hourly_data and len(context.hourly_data[sec]) == 2:
                    # is prev bar an inside bar
                    last_complete = context.hourly_data[sec][1]
                    prev_complete = context.hourly_data[sec][0]
                    if last_complete['high'] < prev_complete['high'] and last_complete['low'] > prev_complete['low']:
                        # now we've determined last bar was inside lets check for hourly breakout
                        if current_prices[sec] > last_complete['high']:
                            context.positions_stop_loss[sec] = last_complete['low']
                            order_value(sec, 10000)
                            print('Entering into ' + str(sec) + '\n60min inside and up\nCurrent Price: ' + str(current_prices[sec]) + '\nPrev Week High: ' + str(
                                context.output['weekly_high'][sec]) + '\nPrev Hour High: ' + str(last_complete['high']))
                            return  # exiting because we are only taking on one position at a time

    current_prices = data.current(context.portfolio.positions.keys(), 'price')
    today_open_sec = data.history(context.portfolio.positions.keys(), "open", 1, "1d")
    for sec in context.portfolio.positions.keys():
        if sec in open_orders:
            continue
        construct_hourly_data(
            sec, exchange_time, context, open_sec, high_sec, low_sec, close_sec)
        if (sec not in current_prices) or (sec not in context.positions_stop_loss):
            print('sec ' + str(sec) + ' not found')
        # we have a stop set so lets see if we're short or long
        elif  context.portfolio.positions[sec].amount > 0:
            # we're long 
            if current_prices[sec] < context.positions_stop_loss[sec]:
                print('Exiting ' + str(sec) + ' due to stop at ' +
                      str(context.positions_stop_loss[sec]))
                # del context.positions_stop_loss[sec]
                order_target(sec, 0)
    
            else:
                # look for full timeframe continuity down
                
                # does this security exist in current pipeline
                # if not we have to calculate the opens historical data
                if sec in context.output['monthly_current_open']:
                    monthly_open = context.output['monthly_current_open'][sec]
                else:
                    monthly_open = get_monthly_open(sec, open_daily_sec, exchange_time)
                if monthly_open == 0:
                    monthly_open = today_open_sec[sec][0]
                
                
                if sec in context.output['weekly_current_open']:
                    weekly_open = context.output['weekly_current_open'][sec]
                else:
                    weekly_open = get_weekly_open(sec, open_daily_sec, exchange_time)
                if weekly_open == 0:
                    weekly_open = today_open_sec[sec][0]
                
                
                if (current_prices[sec] < monthly_open):
                    if (current_prices[sec] < weekly_open):
                        if (current_prices[sec] < today_open_sec[sec][0]):
                            if (current_prices[sec] < context.hourly_current_open[sec]):
                                # look for hourly inside and down breakout
                                if sec in context.hourly_data and len(context.hourly_data[sec]) == 2:
                                    last_complete = context.hourly_data[sec][1]
                                    prev_complete = context.hourly_data[sec][0]
                                    if last_complete['high'] < prev_complete['high'] and last_complete['low'] > prev_complete['low']:
                                        # we have inside bar
                                        # now look for breakout down
                                        if current_prices[sec] < last_complete['low']:
                                            print(
                                                'Exiting ' + str(sec) + ' due to 60min inside and down breakout at ' + str(last_complete['low']))
                                            order_target(sec, 0)   
        else:
            #we're short
            if current_prices[sec] > context.positions_stop_loss[sec]:
                print('Exiting ' + str(sec) + ' due to stop at ' +
                      str(context.positions_stop_loss[sec]))
                # del context.positions_stop_loss[sec]
                order_target(sec, 0)
    
            else:
                if sec in context.output['monthly_current_open']:
                    monthly_open = context.output['monthly_current_open'][sec]
                else:
                    monthly_open = get_monthly_open(sec, open_daily_sec, exchange_time)
                if monthly_open == 0:
                    monthly_open = today_open_sec[sec][0]
                    
                if sec in context.output['weekly_current_open']:
                    weekly_open = context.output['weekly_current_open'][sec]
                else:
                    weekly_open = get_weekly_open(sec, open_daily_sec, exchange_time)
                if weekly_open == 0:
                    weekly_open = today_open_sec[sec][0]
                    
                # look for full timeframe continuity down
                if (current_prices[sec] > monthly_open
                    and current_prices[sec] > weekly_open
                    and current_prices[sec] > today_open_sec[sec][0]
                    and current_prices[sec] > context.hourly_current_open[sec]):
                    # look for hourly inside and down breakout
                    if sec in context.hourly_data and len(context.hourly_data[sec]) == 2:
                        last_complete = context.hourly_data[sec][1]
                        prev_complete = context.hourly_data[sec][0]
                        if last_complete['high'] < prev_complete['high'] and last_complete['low'] > prev_complete['low']:
                            # we have inside bar
                            # now look for breakout down
                            if current_prices[sec] > last_complete['high']:
                                print(
                                    'Exiting ' + str(sec) + ' due to 60min inside and up breakout at ' + str(last_complete['high']))
                                order_target(sec, 0)  

def construct_hourly_data(sec, exchange_time, context, open, high, low, close):
    """
    Construct hourly bars
    """
    try:
        if exchange_time.hour > 9 and exchange_time.minute == 31:
            # time_stamp = '{:02d}'.format(
            # exchange_time.hour) + '{:02d}'.format(exchange_time.minute - 1)
            if sec not in context.hourly_data:
                context.hourly_data[sec] = []

            context.hourly_data[sec].append(
                {
                    'open': open[sec][0],
                    'high': high[sec][:-1].max(),
                    'low': low[sec][:-1].min(),
                    'close': close[sec][-2]
                })
            
            if len(context.hourly_data[sec]) > 2:
                context.hourly_data[sec].pop(0)
        elif exchange_time.minute == 31:
            context.hourly_current_open[sec] = open[sec][-1]
    except:
        print('error in construct hours')

def get_monthly_open(sec, open_daily_sec, exchange_time):

    for dt in open_daily_sec[sec].keys()[::-1]:
        if dt.month != exchange_time.month:
            price = open_daily_sec[sec][dt - 1]
            break
    
    return price
def get_weekly_open(sec, open_daily_sec, exchange_time):
    
    # key off of transitions from 0 to 4
    current_weekday = -1
    last_weekday = 10
    if exchange_time.weekday() > 0:
        for dt in open_daily_sec[sec].keys()[::-1]:
            current_weekday = dt.weekday()
            if current_weekday > last_weekday:
                price = open_daily_sec[sec][dt - 1]
                break
            last_weekday = dt.weekday()
    else:
        price = 0
    return price

class WeeklyGammaFilter(CustomFilter):
    """
    Classifiy weekly bars
    """
    window_length = 14

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Do weekly classification
        """

        today_day = today.weekday()

        current_end_week_idx = -today_day - 1
        current_start_week_idx = -today_day - 5

        prev_end_week_idx = -today_day - 6
        prev_start_week_idx = -today_day - 10

        day_idx = today
        week_count = 0
        # key off of transitions from 0 to 4
        for num in range(-WeeklyGammaFilter.window_length, 0)[::-1]:
            prev_day = day_idx.weekday()
            day_idx = day_idx - 1
            new_day = day_idx.weekday()
            if prev_day <= new_day:
                week_count = week_count + 1
                factor = prev_day - new_day + 4
            else:
                factor = prev_day - new_day - 1

            # check for closings on a monday of week

            if num >= current_end_week_idx:
                if prev_day in [0, 1] and new_day == 4:
                    current_end_week_idx = current_end_week_idx + factor
            if num >= current_start_week_idx:
                current_start_week_idx = current_start_week_idx + factor
            if num >= prev_end_week_idx:
                if prev_day == 0 and new_day == 4 or num >= current_end_week_idx:
                    prev_end_week_idx = prev_end_week_idx + factor
            if num >= prev_start_week_idx:
                prev_start_week_idx = prev_start_week_idx + factor

        current_week_open = open[current_start_week_idx]
        current_week_close = close[current_end_week_idx]

        if current_end_week_idx == -1:
            current_week_high = high[current_start_week_idx:, :].max(
                axis=0)
            current_week_low = low[current_start_week_idx:, :].min(
                axis=0)
        else:
            current_week_high = high[current_start_week_idx:current_end_week_idx + 1, :].max(
                axis=0)

            current_week_low = low[current_start_week_idx:current_end_week_idx + 1, :].min(
                axis=0)

       # prev_week_open = open[prev_start_week_idx]
       # prev_week_close = close[prev_end_week_idx]

        prev_week_high = high[prev_start_week_idx:prev_end_week_idx + 1, :].max(
            axis=0)
        prev_week_low = low[prev_start_week_idx:prev_end_week_idx + 1, :].min(
            axis=0)

        r_alpha = (current_week_high - current_week_low) / ALPHA_DIVISOR
        alpha_z = current_week_high - r_alpha

        r_beta = (current_week_high - current_week_low) / BETA_DIVISOR
        beta_z = current_week_low + r_beta

        # & (current_week_close[-1] > current_week_open[-1])
        is_alpha = (current_week_open > alpha_z) & (
            current_week_close > alpha_z)
        # & (current_week_close[-1] < current_week_open[-1])
        is_beta = (current_week_open < beta_z) & (current_week_close < beta_z)
        is_gamma = (prev_week_high > current_week_high) & (
            prev_week_low < current_week_low)
        is_delta = (prev_week_high < current_week_high) & (
            prev_week_low > current_week_low)

        bar_types = [0] * len(open[-1])
        bar_types = (is_alpha << 1) + bar_types
        bar_types = (is_beta << 2) + bar_types
        bar_types = (is_gamma << 3) + bar_types
        bar_types = (is_delta << 4) + bar_types
        out[:] = ((bar_types == BAR_TYPE['gamma']) |
                  (bar_types == BAR_TYPE['gamma_alpha']) |
                  (bar_types == BAR_TYPE['gamma_beta']))


class WeeklyHigh(CustomFactor):
    """
    Classifiy weekly bars
    """
    window_length = 9

    def compute(self, today, asset_ids, out, high):
        """
            Do weekly classification
        """

        today_day = today.weekday()

        current_end_week_idx = -today_day - 1
        current_start_week_idx = -today_day - 5

        day_idx = today
        week_count = 0
        # key off of transitions from 0 to 4
        for num in range(-WeeklyHigh.window_length, 0)[::-1]:
            prev_day = day_idx.weekday()
            day_idx = day_idx - 1
            new_day = day_idx.weekday()
            if prev_day <= new_day:
                week_count = week_count + 1
                factor = prev_day - new_day + 4
            else:
                factor = prev_day - new_day - 1

            # check for closings on a monday of week

            if num >= current_end_week_idx:
                if prev_day in [0, 1] and new_day == 4:
                    current_end_week_idx = current_end_week_idx + factor
            if num >= current_start_week_idx:
                current_start_week_idx = current_start_week_idx + factor

        if current_end_week_idx == -1:
            current_week_high = high[current_start_week_idx:, :].max(
                axis=0)
        else:
            current_week_high = high[current_start_week_idx:current_end_week_idx + 1, :].max(
                axis=0)

        out[:] = current_week_high


class WeeklyLow(CustomFactor):
    """
    Classifiy weekly bars
    """
    window_length = 9

    def compute(self, today, asset_ids, out, low):
        """
            Do weekly classification
        """

        today_day = today.weekday()

        current_end_week_idx = -today_day - 1
        current_start_week_idx = -today_day - 5

        day_idx = today
        week_count = 0
        # key off of transitions from 0 to 4
        for num in range(-WeeklyLow.window_length, 0)[::-1]:
            prev_day = day_idx.weekday()
            day_idx = day_idx - 1
            new_day = day_idx.weekday()
            if prev_day <= new_day:
                week_count = week_count + 1
                factor = prev_day - new_day + 4
            else:
                factor = prev_day - new_day - 1

            # check for closings on a monday of week

            if num >= current_end_week_idx:
                if prev_day in [0, 1] and new_day == 4:
                    current_end_week_idx = current_end_week_idx + factor
            if num >= current_start_week_idx:
                current_start_week_idx = current_start_week_idx + factor

        if current_end_week_idx == -1:
            # current_week_high = high[current_start_week_idx:, :].max(
            #     axis=0)
            current_week_low = low[current_start_week_idx:, :].min(
                axis=0)
        else:
            # current_week_high = high[current_start_week_idx:current_end_week_idx + 1, :].max(
            #     axis=0)

            current_week_low = low[current_start_week_idx:current_end_week_idx + 1, :].min(
                axis=0)

        out[:] = current_week_low


class CurrentInsideMonthClassifier(CustomFilter):
    """
    Determine if current month is trading within prev months range
    """
    window_length = 61

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Determine if current month is trading within prev months range
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        prev_month = current_month - 1 if current_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        prev_end_month_idx = 0
        prev_start_month_idx = 0

        while idx > -CurrentInsideMonthClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx
            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1

                if prev_end_month_idx == 0:
                    prev_end_month_idx = idx

            if month_idx not in [start_month, current_month, prev_month]:
                if prev_start_month_idx == 0:
                    prev_start_month_idx = idx

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1

        if current_end_month_idx == -1:
            current_month_high = high[current_start_month_idx:, :].max(
                axis=0)
            current_month_low = low[current_start_month_idx:, :].min(
                axis=0)
        else:
            current_month_high = high[current_start_month_idx:current_end_month_idx + 1, :].max(
                axis=0)

            current_month_low = low[current_start_month_idx:current_end_month_idx + 1, :].min(
                axis=0)

        start_month_high = high[current_end_month_idx:, :].max(axis=0)
        start_month_low = low[current_end_month_idx:, :].min(axis=0)
        out[:] = (start_month_high > current_month_high) | (
            start_month_low < current_month_low)


class MonthlyCurrentOpen(CustomFactor):
    """
    Get the open for the current incomplete monthly bar
    """
    window_length = 32

    def compute(self, today, asset_ids, out, open):
        """
            Compute the open for the current incomplete monthly bar
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        while idx > -MonthlyCurrentOpen.window_length:
            if month_idx == current_month:
                idx = idx + 1
                break

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1
        if idx == 0:
            out[:] = 0
        else:
            out[:] = open[idx]
            
class WeeklyCurrentOpen(CustomFactor):
    """
    WeeklyCurrentOpen
    """
    window_length = 5

    def compute(self, today, asset_ids, out, open):
        """
            WeeklyCurrentOpen
        """
        start_week_idx = -1;
        day_idx = today
        # key off of transitions from 0 to 4
        for num in range(-WeeklyCurrentOpen.window_length, 0)[::-1]:
            prev_day = day_idx.weekday()
            day_idx = day_idx - 1
            new_day = day_idx.weekday()
            if prev_day <= new_day:
                start_week_idx = num + 1
                break

        if start_week_idx == 0:
            out[:] = 0
        else:
            out[:] = open[start_week_idx]