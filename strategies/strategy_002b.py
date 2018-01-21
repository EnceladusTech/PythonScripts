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
CLOSE_PRICE_MIN_AVG = 10.0
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

    to_exclude_symbol_filter = StaticSids([sid(40515), sid(41969), sid(38054)])
    sp_100_filter = StaticSids(getSP100())
   # exchange = Fundamentals.exchange_id.latest
    # nyse_filter = exchange.eq('NYS')

    # dollar_volume = AverageDollarVolume(window_length=10)
    # high_dollar_volume = dollar_volume.top(TOP_NUM_STOCKS_BY_DOLLAR_VOLUME)
    vol_sma = SimpleMovingAverage(
        inputs=[USEquityPricing.volume], window_length=90)
    price_sma = SimpleMovingAverage(
        inputs=[USEquityPricing.close], window_length=30)

    vol_filter = ~(to_exclude_symbol_filter) & (vol_sma > VOLUME_MIN_AVG) & (price_sma > CLOSE_PRICE_MIN_AVG)


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

    monthly_outside_filter = MonthlyOutsideFilter(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        mask=vol_filter
    )

    monthly_current_open = MonthlyCurrentOpen(
        inputs=[USEquityPricing.open],
        mask=vol_filter
    )
    weekly_current_open = WeeklyCurrentOpen(
        inputs=[USEquityPricing.open],
        mask=vol_filter
    )

    pipe = Pipeline(
        screen=(weekly_gamma_filter) & (monthly_outside_filter),
        # screen = symbol_filter,
        columns={
            # 'daily_classifier': daily_classifier,
            # 'daily_high': USEquityPricing.high.latest,
            # 'daily_low': USEquityPricing.low.latest,
            'weekly_gamma_filter': weekly_gamma_filter,
            'monthly_outside_filter': monthly_outside_filter,
            'weekly_high': weekly_high,
            'weekly_low': weekly_low,
            'monthly_current_open': monthly_current_open,
            'weekly_current_open': weekly_current_open,
            'is_sp_100': sp_100_filter
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


def record_counts(context, data):

    longs = len(filter(lambda sec: context.portfolio.positions[sec].amount > 0,  context.portfolio.positions.keys()))
    shorts = len(filter(lambda sec: context.portfolio.positions[sec].amount < 0,  context.portfolio.positions.keys()))
    total = len(context.portfolio.positions)
    open_orders = len(get_open_orders())
    record(
        long_pos=longs,
        short_pos=shorts,
        total_pos = total,
        total_open_orders = open_orders
    )

def handle_data(context, data):
    """
    Called every minute.
    """

    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    if exchange_time.hour > 15:
        return ''
    if exchange_time.hour == 15 and exchange_time.minute > 45:
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
        pos_count = len(context.portfolio.positions) + len(open_orders)

        if pos_count >= 10:
            continue
            
        monthly_open = context.output['monthly_current_open'][sec]
        if monthly_open == 0:
            monthly_open = today_open[sec][0]
                
        weekly_open = context.output['weekly_current_open'][sec]
        if weekly_open == 0:
            weekly_open = today_open[sec][0]
            
        # Should be trading outside prev months range and be an inside week at this point
        # make sure we have full timeframe continuity i.e. trading above all opens of each timeframe
        if (context.output['is_sp_100'][sec]
            and current_prices[sec] > monthly_open
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
                            context.positions_stop_loss[sec] = context.output['weekly_low'][sec]
                            order_value(sec, 10000)
                            log.info(',' + str(exchange_time) + ',long entry,' + str(sec) + ',60min inside and up')
                            # log.info('++++++\nEntering long for ' + str(sec) + 
                            #       '\n60min inside and up\nCurrent Price: ' + str(current_prices[sec]) + 
                            #       '\nLast Week High,Low: [' + str(context.output['weekly_high'][sec]) + ', ' + str(context.output['weekly_low'][sec]) + ']' +
                            #       '\nLast Hour OHLC: [' + str(last_complete['open']) + ', '+ str(last_complete['high']) + ', '+ str(last_complete['low']) + ', '+ str(last_complete['close']) + ']' +
                            #       '\nPrev Hour OHLC: [' + str(prev_complete['open']) + ', '+ str(prev_complete['high']) + ', '+ str(prev_complete['low']) + ', '+ str(prev_complete['close']) + ']' +
                            #       '\nStop set at Last Week Low: ' + str(context.output['weekly_low'][sec]) )                           
        elif (current_prices[sec] < monthly_open
            and current_prices[sec] < weekly_open
            and current_prices[sec] < today_open[sec][0]
            and current_prices[sec] < context.hourly_current_open[sec]):
            if current_prices[sec] < context.output['weekly_low'][sec]:
                # we've broken out of the week now test the hour
                if sec in context.hourly_data and len(context.hourly_data[sec]) == 2:
                    # is prev bar an inside bar
                    last_complete = context.hourly_data[sec][1]
                    prev_complete = context.hourly_data[sec][0]
                    if last_complete['high'] < prev_complete['high'] and last_complete['low'] > prev_complete['low']:
                        # now we've determined last bar was inside lets check for hourly breakout
                        if current_prices[sec] < last_complete['low']:
                            context.positions_stop_loss[sec] = context.output['weekly_high'][sec]
                            order_value(sec, -10000)
                            log.info(',' + str(exchange_time) + ',short entry,' + str(sec) + ',60min inside and down')
                            # log.info('++++++\nEntering short for ' + str(sec) + 
                            #       '\n60min inside and down\nCurrent Price: ' + str(current_prices[sec]) + 
                            #       '\nLast Week High,Low: [' + str(context.output['weekly_high'][sec]) + ', ' + str(context.output['weekly_low'][sec]) + ']' +
                            #       '\nLast Hour OHLC: [' + str(last_complete['open']) + ', '+ str(last_complete['high']) + ', '+ str(last_complete['low']) + ', '+ str(last_complete['close']) + ']' +
                            #       '\nPrev Hour OHLC: [' + str(prev_complete['open']) + ', '+ str(prev_complete['high']) + ', '+ str(prev_complete['low']) + ', '+ str(prev_complete['close']) + ']' +
                            #       '\nStop set at Last Week high: ' + str(context.output['weekly_high'][sec]) )      
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
                log.info(',' + str(exchange_time) + ',long exit,' + str(sec) + ',stop loss')
                # print('------\nExiting ' + str(sec) + ' due to stop at ' +
                #       str(context.positions_stop_loss[sec]))
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
                
                
                if (current_prices[sec] < monthly_open 
                    and current_prices[sec] < weekly_open 
                    and current_prices[sec] < today_open_sec[sec][0]
                    and current_prices[sec] < context.hourly_current_open[sec]):
                     # look for hourly inside and down breakout
                    if sec in context.hourly_data and len(context.hourly_data[sec]) == 2:
                        last_complete = context.hourly_data[sec][1]
                        prev_complete = context.hourly_data[sec][0]
                        if last_complete['high'] < prev_complete['high'] and last_complete['low'] > prev_complete['low']:
                            # we have inside bar
                            # now look for breakout down
                            if current_prices[sec] < last_complete['low']:
                                log.info(',' + str(exchange_time) + ',long exit,' + str(sec) + ',60min inside and down')
                                # log.info('------\nExiting long pos for ' + str(sec) + 
                                #       '\n60min inside and down\nCurrent Price: ' + str(current_prices[sec]) + 
                                #       '\nLast Hour OHLC: [' + str(last_complete['open']) + ', '+ str(last_complete['high']) + ', '+ str(last_complete['low']) + ', '+ str(last_complete['close']) + ']' +
                                #       '\nPrev Hour OHLC: [' + str(prev_complete['open']) + ', '+ str(prev_complete['high']) + ', '+ str(prev_complete['low']) + ', '+ str(prev_complete['close']) + ']' +
                                #       '\nBreakout occurred below: ' + str(last_complete['low']) )   
                                order_target(sec, 0)   
        else:
            #we're short
            if current_prices[sec] > context.positions_stop_loss[sec]:
                log.info(',' + str(exchange_time) + ',short exit,' + str(sec) + ',stop loss')
                # print('------\nExiting ' + str(sec) + ' due to stop at ' +
                #       str(context.positions_stop_loss[sec]))
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
                    
                # look for full timeframe continuity up
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
                                log.info(',' + str(exchange_time) + ',short exit,' + str(sec) + ',60min inside and up')
                                # log.info('------\nExiting short pos for ' + str(sec) + 
                                #       '\n60min inside and down\nCurrent Price: ' + str(current_prices[sec]) + 
                                #       '\nLast Hour OHLC: [' + str(last_complete['open']) + ', '+ str(last_complete['high']) + ', '+ str(last_complete['low']) + ', '+ str(last_complete['close']) + ']' +
                                #       '\nPrev Hour OHLC: [' + str(prev_complete['open']) + ', '+ str(prev_complete['high']) + ', '+ str(prev_complete['low']) + ', '+ str(prev_complete['close']) + ']' +
                                #       '\nBreakout occurred above: ' + str(last_complete['high']) )
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
    window_length = 19

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Do weekly classification
        """

        today_day = today.weekday()

        current_end_week_idx = -today_day - 1
        current_start_week_idx = -today_day - 5

        prev_end_week_idx = -today_day - 6
        prev_start_week_idx = -today_day - 10

        two_ago_end_week_idx = -today_day - 11
        two_ago_start_week_idx = -today_day - 15

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

            if num >= two_ago_end_week_idx:
                two_ago_end_week_idx = two_ago_end_week_idx + factor
            if num >= two_ago_start_week_idx:
                two_ago_start_week_idx = two_ago_start_week_idx + factor

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

        two_ago_week_high = high[two_ago_start_week_idx:two_ago_end_week_idx + 1, :].max(
            axis=0) 
        two_ago_week_low = low[two_ago_start_week_idx:two_ago_end_week_idx + 1, :].min(
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
        
        is_any_gamma = ((bar_types == BAR_TYPE['gamma']) |
                  (bar_types == BAR_TYPE['gamma_alpha']) |
                  (bar_types == BAR_TYPE['gamma_beta']))

        is_current_week_preceded_by_outside_week = (prev_week_high > two_ago_week_high) & (prev_week_low < two_ago_week_low)


        out[:] = (is_any_gamma) & ~(is_current_week_preceded_by_outside_week)

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

class MonthlyOutsideFilter(CustomFilter):
    """
    Classifiy monthly bars
    """
    window_length = 92

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Do monthly classification
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

        while idx > -MonthlyOutsideFilter.window_length:
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

        current_month_open = open[current_start_month_idx]
        current_month_close = close[current_end_month_idx]

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
       # prev_month_open = open[prev_start_month_idx]
       # prev_month_close = close[prev_end_month_idx]

        prev_month_high = high[prev_start_month_idx:
                               prev_end_month_idx + 1, :].max(axis=0)
        prev_month_low = low[prev_start_month_idx:
                             prev_end_month_idx + 1, :].min(axis=0)

        r_alpha = (current_month_high - current_month_low) / ALPHA_DIVISOR
        alpha_z = current_month_high - r_alpha

        r_beta = (current_month_high - current_month_low) / BETA_DIVISOR
        beta_z = current_month_low + r_beta

        # & (current_month_close[-1] > current_month_open[-1])
        is_alpha = (current_month_open > alpha_z) & (
            current_month_close > alpha_z)
        # & (current_month_close[-1] < current_month_open[-1])
        is_beta = (current_month_open < beta_z) & (
            current_month_close < beta_z)
        is_gamma = (prev_month_high < current_month_high) & (
            prev_month_low > current_month_low)
        is_delta = (prev_month_high > current_month_high) & (
            prev_month_low < current_month_low)

        bar_types = [0] * len(open[-1])
        bar_types = (is_alpha << 1) + bar_types
        bar_types = (is_beta << 2) + bar_types
        bar_types = (is_gamma << 3) + bar_types
        bar_types = (is_delta << 4) + bar_types
        out[:] = ~((bar_types == BAR_TYPE['delta']) |
                  (bar_types == BAR_TYPE['delta_alpha']) |
                  (bar_types == BAR_TYPE['delta_beta']))


def getSP100(context):
    return [
    sid(24),    # AAPL,  APPLE INC
    sid(43694), # ABBV
    sid(62),    # ABT,   ABBOTT LABORATORIES
    sid(25555), # ACN,   ACCENTURE PLC
    sid(205),   # AGN,
    #sid(161),   # AEP,   AMERICAN ELECTRIC POWER INC
    sid(239),   # AIG,   AMERICAN INTL GROUP INC
    sid(24838), # ALL,   ALLSTATE CORP (THE)
    sid(368),   # AMGN,  AMGEN INC
    sid(16841), # AMZN,  AMAZON.COM INC
    #sid(448),   # APA,   APACHE CORP
    #sid(455),   # APC,   ANADARKO PETROLEUM CORP
    sid(679),   # AXP,   AMERICAN EXPRESS COMPANY
    sid(698),   # BA,    BOEING CO
    sid(700),   # BAC,   BANK OF AMERICA CORP
    sid(3806),  #BIIB,
    #sid(734),   # BAX,   BAXTER INTERNATIONAL INC
    sid(903),   # BK,    BANK OF NEW YORK MELLON CORP/T
    sid(20689), # BLK,
    sid(980),   # BMY,   BRISTOL MYERS SQUIBB COMPANY
    sid(11100), # BRK.B, BERKSHIRE HATHWY INC(HLDG CO) B
    sid(1335),  # C,     CITIGROUP
    sid(1267),  # CAT,   CATERPILLAR INC
    sid(1406), # CELG,
    sid(20838), #CHTR,
    sid(1582),  # CL,    COLGATE-PALMOLIVE CO
    sid(1637), #CMCSA	Comcast Corporation
    sid(12160), # COF,   CAPITAL ONE FINANCIAL CORP
    sid(23998), # COP,   CONOCOPHILLIPS
    sid(1787),  # COST,  COSTCO WHOLESALE CORP
    sid(1900),  # CSCO,  CISCO SYSTEMS INC
    #sid(1971),  # CTS,   CTS CORP
    sid(4799),  # CVS,   CVS CAREMARK CORP
    sid(23112), # CVX,   CHEVRON CORPORATION
    #sid(2119),  # DD,    DU PONT DE NEMOURS E I &CO
    #sid(25317), # DELL,  DELL INC
    sid(2170),      # DHR	Danaher
    sid(2190),  # DIS,   WALT DISNEY CO-DISNEY COMMON
    sid(2351),      #DUK	Duke Energy
    sid(51157),      #DWDP	DowDuPont
    #sid(2263),  # DOW,   DOW CHEMICAL CO
    #sid(2368),  # DVN,   DEVON ENERGY CORP (NEW)
    #sid(24819), # EBAY,  EBAY INC
    #sid(2518),  # EMC,   EMC CORPORATION
    sid(2530),  # EMR,   EMERSON ELECTRIC CO
    sid(22114), # EXC,   EXELON CORPORATION
    sid(2673),  # F,     FORD MOTOR CO(NEW)
    sid(42950),  #FB	Facebook
    #sid(13197), # FCX,   FREEPORT-MCMORAN COPPER&GOLD B
    sid(2765),  # FDX,   FEDEX CORPORATION
    sid(5530),      #FOX	21st Century Fox
    sid(12213),      #FOXA	21st Century Fox
    sid(3136),  # GD,    GENERAL DYNAMICS CORP
    sid(3149),  # GE,    GENERAL ELECTRIC CO
    sid(3212),  # GILD,  GILEAD SCIENCES INC
    sid(3246),  # GM,    GENERAL MOTORS CORP
    sid(46631), # GOOG,  GOOGLE INC,
    sid(26578),      # GOOGL	Alphabet Inc
    sid(20088), # GS,    GOLDMAN SACHS GROUP INC
    sid(3443),  # HAL,   HALLIBURTON CO (HOLDING CO)
    sid(3496),  # HD,    HOME DEPOT INC
    sid(25090), # HON,   HONEYWELL INTERNATIONAL INC
    #sid(3735),  # HPQ,   HEWLETT-PACKARD CO
    sid(3766),  # IBM,   INTL BUSINESS MACHINES CORP
    sid(3951),  # INTC,  INTEL CORP
    sid(4151),  # JNJ,   JOHNSON AND JOHNSON
    sid(25006), # JPM,   JPMORGAN CHASE & CO COM STK
    sid(49229),      #KHC	Kraft Heinz
    sid(20744),      #KMI	Kinder Morgan Inc/DE **KMI has 2 ids in quantopia
    sid(40852),          #KMI Kinder Morgan Inc/DE *KMI has 2 ids in quantopia
    sid(4283),  # KO,    COCA-COLA CO
    sid(4487),  # LLY,   LILLY ELI & CO
    sid(12691), # LMT,   LOCKHEED MARTIN CORP
    sid(4521),  # LOW,   LOWES COMPANIES INC
    sid(32146), # MA,    MASTERCARD INC
    sid(4707),  # MCD,   MCDONALDS CORP
    sid(22802), # MDLZ,  MONDELEZ INTERNATIONAL INC
    sid(4758),  # MDT,   MEDTRONIC INC
    sid(21418), # MET,   METLIFE  INC
    sid(4922),  # MMM,   3M COMPANY
    sid(4954),  # MO,    ALTRIA GROUP INC.
    sid(22140), # MON,   MONSANTO COMPANY
    sid(5029),  # MRK,   MERCK & CO INC
    sid(17080), # MS,    MORGAN STANLEY
    sid(5061),  # MSFT,  MICROSOFT CORP
    sid(2968),      #NEE	NextEra Energy
    sid(5328),  # NKE,   NIKE INC CL-B
    #sid(24809), # NOV,   NATIONAL OILWELL VARCO  INC.
    #sid(5442),  # NSC,   NORFOLK SOUTHERN CORP
    #sid(12213), # NWSA,  NEWS CP - CL A
    sid(5692),  # ORCL,  ORACLE CORP
    sid(5729),  # OXY,   OCCIDENTAL PETROLEUM CORP
    sid(19917),      #PCLN	Priceline Group Inc/The
    sid(5885),  # PEP,   PEPSICO INC
    sid(5923),  # PFE,   PFIZER INC
    sid(5938),  # PG,    PROCTER & GAMBLE CO
    sid(35902), # PM,    PHILIP MORRIS INTERNATIONAL INC
    sid(49242),      #PYPL	PayPal Holdings
    sid(6295),  # QCOM,  QUALCOMM INC
    sid(6583),  # RTN,   RAYTHEON CO. (NEW)
    sid(6683),  # SBUX,  STARBUCKS CORPORATION
    sid(6928),  # SLB,   SCHLUMBERGER LTD
    sid(7011),  # SO,    SOUTHERN CO
    sid(10528), # SPG,   SIMON PROPERTIES GROUP INC
    sid(6653),  # T,     AT&T INC. COM
    sid(21090), # TGT,   TARGET CORPORATION
    sid(357),   # TWX,   TIME WARNER INC.
    sid(7671),  # TXN,   TEXAS INSTRUMENTS INC
    sid(7792),  # UNH,   UNITEDHEALTH GROUP INC
    sid(7800),  # UNP,   UNION PACIFIC CORPORATION
    sid(20940), # UPS,   UNITED PARCEL SERVICE INC.CL B
    sid(25010), # USB,   U.S.BANCORP (NEW)
    sid(7883),  # UTX,   UNITED TECHNOLOGIES CORP
    sid(35920), # V,     VISA INC
    sid(21839), # VZ,    VERIZON COMMUNICATIONS
    #sid(8089),  # WAG,   WALGREEN COMPANY
    sid(8089),       #WBA	Walgreens Boots Alliance
    sid(8151),  # WFC,   WELLS FARGO & CO(NEW)d
    #sid(8214),  # WMB,   WILLIAMS COMPANIES
    sid(8229),  # WMT,   WAL-MART STORES INC
    sid(8347),  # XOM,   EXXON MOBIL CORPORATION
    ]
