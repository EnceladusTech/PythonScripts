"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import CustomFactor, Pipeline, CustomFilter
import numpy as np
from datetime import datetime as DateTime, timedelta as TimeDelta
from quantopian.pipeline.data.builtin import USEquityPricing
from pytz import timezone
from quantopian.pipeline.filters import Q1500US
import quantopian.optimize as opt

bar_type = {
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


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # referencing SPY so the 'handle_data' function will be called every minute
    #context.spy = sid(8554)

    context.intraday_bars = {}
    context.target_weights = {}
    context.daily_stat_history = []
    context.positions_stop_loss = {}
    context.positions_max_gain = {}
 #   schedule_function(
 #       open_positions,
 #       date_rules.every_day(),
 #       time_rules.market_open()
 #   )

   # schedule_function(
   #     close_positions,
   #     date_rules.every_day(),
   #     time_rules.market_close(hours=0.5)
   # )

    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    # Base universe set to the Q1500US.
    base_universe = Q1500US()
    # alpha_long_daily = AlphaLongDaily(
    #     inputs=[
    #         USEquityPricing.open,
    #         USEquityPricing.high,
    #         USEquityPricing.low,
    #         USEquityPricing.close
    #     ],
    #     window_length=1,
    #     mask=base_universe
    # )
    # alpha_long_weekly = AlphaLongWeekly(
    #     inputs=[
    #         USEquityPricing.open,
    #         USEquityPricing.high,
    #         USEquityPricing.low,
    #         USEquityPricing.close
    #     ],
    #     window_length=9,
    #     mask=base_universe
    # )
    volume_filter = VolumeFilter(
         inputs=[USEquityPricing.volume],
         window_length=1,
         mask=base_universe
     )

    # is_setup = volume_filter & alpha_long_weekly & alpha_long_daily

    daily_classifier = DailyClassifier(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        mask=volume_filter

    )

    pipe = Pipeline(
        screen=volume_filter & (daily_classifier > 0),
        columns={
            'daily_classifier': daily_classifier,
            'daily_high': USEquityPricing.high.latest,
            'daily_low': USEquityPricing.low.latest
        }
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
    context.current_stock_list =  context.output.index.tolist()
    
    context.daily_stat_history.append(context.output)
    if len(context.daily_stat_history) > 2:  # only keep last two units
       context.daily_stat_history.pop(0)

    #print context.output['daily_classifier']
    sig_counts = context.output['daily_classifier'].value_counts()
    if 2.0 not in sig_counts.index:
        sig_counts[2.0] = 0.0
    if 4.0 not in sig_counts.index:
        sig_counts[4.0] = 0.0
    if 8.0 not in sig_counts.index:
        sig_counts[8.0] = 0.0
    if 10.0 not in sig_counts.index:
        sig_counts[10.0] = 0.0
    if 12.0 not in sig_counts.index:
        sig_counts[12.0] = 0.0
    if 16.0 not in sig_counts.index:
        sig_counts[16.0] = 0.0
    if 18.0 not in sig_counts.index:
        sig_counts[18.0] = 0.0
    if 20.0 not in sig_counts.index:
        sig_counts[20.0] = 0.0
    record(
        alpha=sig_counts[2.0],
        beta=sig_counts[4.0],
       # gamma=sig_counts[8.0],
        gamma_alpha=sig_counts[10.0],
        gamma_beta=sig_counts[12.0],
        delta=sig_counts[16.0])
       # delta_alpha= sig_counts[18.0],
       # delta_beta= sig_counts[20.0])


def handle_data(context, data):
    """
    Called every minute.
    """

    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
   # print exchange_time
    # TODO
    #    WE WILL BE LOOKING FOR 3 COINCINDING INDICATORS
    #    TWO COULD BE CONSIDERED WEEKLY AND DAILY
    #    THOSE ARE CALCULATED IN THE PIPELINE
#
#    iterate through each in pipeline
#    construct bars as time goes on then check properties of those bars
#

    ##### LOOK FOR NEW POSITIONS TO TAKE ####

    context.longs = []
    context.shorts = []
    open_orders = get_open_orders()
    current_prices = data.current(context.current_stock_list, 'price')
    for sec in context.current_stock_list:
        if data.can_trade(sec):
            if sec not in open_orders and sec not in context.portfolio.positions and context.output['daily_classifier'][sec] == bar_type['alpha'] and context.output['daily_high'][sec] < current_prices[sec]:   
                print 'opening ' + sec.symbol + ' for Alpha thresh_price=' + str(context.output['daily_high'][sec]) + ' triggered_price=' + str(current_prices[sec]) + ' @ '  + str(exchange_time)
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['daily_low'][sec]
                order_target_percent(sec, 0.05)


    ##### LOOK AT CURRENT POSITIONS TO DETERMINE IF EXITS ARE NEEDED ####
                
                
    for pos in context.portfolio.positions.itervalues():
        # check stop loss
        if pos.sid not in open_orders and pos.sid in current_prices and pos.amount > 0:           
            if current_prices[pos.sid] < context.positions_stop_loss[pos.sid]:
                print 'exiting ' + pos.sid.symbol + ' due to stop loss at ' + str(context.positions_stop_loss[pos.sid])
                order_target_percent(pos.sid, 0)
            # check trailing stop
            context.positions_max_gain[pos.sid] = max(current_prices[pos.sid], context.positions_max_gain[pos.sid])
            pct_change = (current_prices[pos.sid] - context.positions_max_gain[pos.sid]) / context.positions_max_gain[pos.sid] 
            if pct_change < -0.1:
                print 'exiting ' + pos.sid.symbol + ' due to trailing stop of ' + str(pct_change) + '% off of ' + str(context.positions_max_gain[pos.sid])
                order_target_percent(pos.sid, 0)
    
        
    # for sec in pipe_results[pipe_results['shorts']].index.tolist():
    #    if data.can_trade(sec):
    #        context.shorts.append(sec)




   # for sec in context.output.index.tolist():
    #    if data.can_trade(sec):
    # context.intraday_bars[sec][

    # Calculate target weights to rebalance
    # compute_target_weights_and_stop_losses(context, data)
    # # If we have target weights, rebalance our portfolio
    # if context.target_weights:
    #     order_optimal_portfolio(
    #         objective=opt.TargetWeights(context.target_weights),
    #         constraints=[],
    #     )

    # Check stop loss
   # for security in context.portfolio.positions:
   #     if security.amount > 0 and context.stop_losses[security] > data.current(security, 'price')
        # we've breeched our stop loss so let close this position
pass


def compute_target_weights_and_stop_losses(context, data):
    """
    Compute ordering weights.
    """

    # If there are securities in our longs and shorts lists,
    # compute even target weights for each security.
    if context.longs and context.shorts:
        long_weight = 0.5 / len(context.longs)
        short_weight = -0.5 / len(context.shorts)
    elif context.longs and not context.shorts:
        long_weight = 1.0 / len(context.longs)
    elif context.shorts and not context.longs:
        short_weight = -1.0 / len(context.shorts)

    # Exit positions in our portfolio if they are not
    # in our longs or shorts lists.
    for security in context.portfolio.positions:
        if security not in context.longs and security not in context.shorts and data.can_trade(security):
            context.target_weights[security] = 0

    for security in context.longs:
        context.target_weights[security] = long_weight
        context.stop_losses[security] = context.output['daily_stops'][security]

    for security in context.shorts:
        context.target_weights[security] = short_weight
def open_positions(context, data):

    # Calculate target weights to rebalance
    compute_target_weights_and_stop_losses(context, data)
    # If we have target weights, rebalance our portfolio
    if context.target_weights:
        order_optimal_portfolio(
            objective=opt.TargetWeights(context.target_weights),
            constraints=[],
        )
def close_positions(context, data):

        # Exit positions in our portfolio if they are not
    # in our longs or shorts lists.
    target_weights = {}
    for security in context.portfolio.positions:
        target_weights[security] = 0
    # Calculate target weights to rebalance

    # If we have target weights, rebalance our portfolio
    if target_weights:
        order_optimal_portfolio(
            objective=opt.TargetWeights(target_weights),
            constraints=[],
        )
class DailyClassifier(CustomFactor):
    window_length = 2

    def compute(self, today, asset_ids, out, open, high, low, close):
        r = (high[-1] - low[-1]) / 3
        alpha_z = high[-1] - r
        beta_z = low[-1] + r

        is_alpha = (open[-1] > alpha_z) & (close[-1] > alpha_z) & (close[-1] > open[-1])
        is_beta = (open[-1] < beta_z) & (close[-1] < beta_z) & (close[-1] < open[-1])
        is_gamma = (high[-1] < high[0]) & (low[-1] > low[0])
        is_delta = (high[-1] > high[0]) & (low[-1] < low[0])

        bar_types = [0] * len(open[-1])
        bar_types = (is_alpha << 1) + bar_types
        bar_types = (is_beta << 2) + bar_types
        bar_types = (is_gamma << 3) + bar_types
        bar_types = (is_delta << 4) + bar_types
        out[:] = bar_types
class VolumeFilter(CustomFilter):
    def compute(self, today, asset_ids, out, volume):
        out[:] = volume[0] > 400000
class AlphaLongDaily(CustomFilter):
    def compute(self, today, asset_ids, out, open, high, low, close):
        r = (high[0] - low[0]) / 3
        z = high[0] - r
        isSetup = (open[0] > z) & (close[0] > z) & (close[0] > open[0])
        out[:] = isSetup
class AlphaLongWeekly(CustomFilter):
    def compute(self, today, asset_ids, out, open, high, low, close):
        todayDay = today.weekday()
        endWeekIdx = 8 - todayDay
        startWeekIdx = 4 - todayDay

        weekOpen = open[startWeekIdx]
        weekClose = close[endWeekIdx]

        weekHigh = high[startWeekIdx:endWeekIdx, :].max(axis=0)
        weekLow = low[startWeekIdx:endWeekIdx, :].min(axis=0)
        r = (weekHigh - weekLow) / 3
        z = weekHigh - r
        is_setup = (weekOpen > z) & (weekClose > z) & (weekClose > weekOpen)
        out[:] = is_setup