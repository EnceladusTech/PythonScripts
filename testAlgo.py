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

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    #referencing SPY so the 'handle_data' function will be called every minute
    context.spy = sid(8554)  
    
    context.stop_losses = {}
    context.intraday_bars = {}
    context.target_weights = {}
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
    alpha_long_daily = AlphaLongDaily(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        window_length=1,
        mask=base_universe
    )
    alpha_long_weekly = AlphaLongWeekly(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        window_length=9,
        mask=base_universe
    )
    volume_filter = VolumeFilter(
        inputs=[USEquityPricing.volume],
        window_length=1,
        mask=base_universe
    )

    is_setup = volume_filter & alpha_long_weekly & alpha_long_daily
    pipe = Pipeline(
        screen=is_setup,
        columns={
            'daily_stops': USEquityPricing.low.latest
        }
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')

    # These are the securities that we are interested in trading each day.
    #context.security_list = context.output.index
    context.longs = []
    
    for sec in context.output.index.tolist():
        if data.can_trade(sec):
            context.longs.append(sec)
            
    context.shorts = []
    #for sec in pipe_results[pipe_results['shorts']].index.tolist():
    #    if data.can_trade(sec):
    #        context.shorts.append(sec)
    
    record(numSetupStocks=len(context.output))
    
def handle_data(context, data):
    """
    Called every minute.
    """
    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))  
    print exchange_time
    # TODO
    #    WE WILL BE LOOKING FOR 3 COINCINDING INDICATORS
    #    TWO COULD BE CONSIDERED WEEKLY AND DAILY
    #    THOSE ARE CALCULATED IN THE PIPELINE
#
#    iterate through each in pipeline
#    construct bars as time goes on then check properties of those bars
#
   # for sec in context.output.index.tolist():
    #    if data.can_trade(sec):
           # context.intraday_bars[sec][
             
    
    
    
    
        # Calculate target weights to rebalance
    compute_target_weights_and_stop_losses(context, data)
    # If we have target weights, rebalance our portfolio
    if context.target_weights:
        order_optimal_portfolio(
            objective=opt.TargetWeights(context.target_weights),
            constraints=[],
        )
    
    
    
    # Check stop loss
   # for security in context.portfolio.positions:
   #     if security.amount > 0 and context.stop_losses[security] > data.current(security, 'price')
            # we've breeched our stop loss so let close this position
            
            
            
def set_trailing_stop(context, data):
    if context.portfolio.positions[context.stock].amount:
        price = data[context.stock].price
        context.stop_price = max(context.stop_price, context.stop_pct * price)
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
        
                
class VolumeFilter(CustomFilter):
    def compute(self, today, asset_ids, out, volume):
        out[:] = volume[0] > 150000
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

        