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

    context.trade_gamma_long = False
    context.trade_gamma_short = False
    context.gamma_daily_breakout_long = 0
    context.gamma_daily_breakout_short = 0
    context.gamma_daily_bar = 0

    context.trade_alpha = True
    context.alpha_daily_breakout = 0
    context.alpha_daily_bar = 0
    context.alpha_weekly_breakout = 0
    context.alpha_weekly_bar = 0

    context.trade_beta = False
    context.beta_daily_breakout = 0
    context.beta_daily_bar = 0

    context.positions_stop_loss = {}
    context.positions_max_gain = {}
    context.position_logs = {}

    context.daily_stat_history = []
    context.hourly_data = {}

    # Record variables at the end of each day.
    schedule_function(log_trade_info,
                      date_rules.every_day(),
                      time_rules.market_close())

    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
    print('datetime,signal,symbol,breakout_thresh,breakout_price,stop_loss\r')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
   # exchange = Fundamentals.exchange_id.latest
   # nyse_filter = exchange.eq('NYS')

    volume_filter = VolumeFilter(
        inputs=[USEquityPricing.volume],
        window_length=1#,
        #mask=nyse_filter
    )

    # is_setup = volume_filter & alpha_long_weekly & alpha_long_daily
    weekly_high = WeeklyHigh(
        inputs=[USEquityPricing.high],
        mask=volume_filter
    )
    weekly_low = WeeklyLow(
        inputs=[USEquityPricing.low],
        mask=volume_filter
    )
    weekly_classifier = WeeklyClassifier(
        inputs=[
            USEquityPricing.open,
            USEquityPricing.high,
            USEquityPricing.low,
            USEquityPricing.close
        ],
        mask=volume_filter
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
    # monthly_high = MonthlyHigh(
    #     inputs=[USEquityPricing.high],
    #     mask=volume_filter
    # )
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
    current_inside_month_classifier = CurrentInsideMonthClassifier(
        inputs=[
            USEquityPricing.high,
            USEquityPricing.low
        ],
        mask=volume_filter
    )
    pipe = Pipeline(
        screen=(current_inside_month_classifier &
                (weekly_classifier == BAR_TYPE['gamma'] or
                 weekly_classifier == BAR_TYPE['gamma_alpha'] or
                 weekly_classifier == BAR_TYPE['gamma_beta'])),
        columns={
            # 'daily_classifier': daily_classifier,
            # 'daily_high': USEquityPricing.high.latest,
            # 'daily_low': USEquityPricing.low.latest,
            'weekly_classifier': weekly_classifier,
            'weekly_high': weekly_high,
            'weekly_low': weekly_low
        }
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
    context.current_stock_list = context.output.index.tolist()
    print(len(context.current_stock_list))
    context.daily_stat_history.append(context.output)
    if len(context.daily_stat_history) > 2:  # only keep last two units
        context.daily_stat_history.pop(0)

    # print context.output['daily_classifier']
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
   # record(
        # alpha=sig_counts[2.0],
        # beta=sig_counts[4.0],
        # gamma=sig_counts[8.0],
        # gamma_alpha=sig_counts[10.0],
        # gamma_beta=sig_counts[12.0]
        # delta=sig_counts[16.0])
        # delta_alpha= sig_counts[18.0],
        # delta_beta= sig_counts[20.0])


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

    today_open = data.history(context.current_stock_list, "open", 1, "1d")
    current_prices = data.current(context.current_stock_list, 'price')
    for sec in context.current_stock_list:
        # build intraday bars
        if exchange_time.hour > 9 and exchange_time.minute == 31:
            # time_stamp = '{:02d}'.format(
                # exchange_time.hour) + '{:02d}'.format(exchange_time.minute - 1)
            if sec not in context.hourly_data:
                context.hourly_data[sec] = {}
            opens = data.history(
                context.current_stock_list, "open", 61, "1m", )
            highs = data.history(
                context.current_stock_list, "high", 61, "1m", )
            lows = data.history(context.current_stock_list, "low", 61, "1m", )
            closes = data.history(
                context.current_stock_list, "close", 61, "1m", )
            high = highs[:-1].max()
            low = lows[:-1].min()
            context.hourly_data[sec][exchange_time] = [
                opens[0], high, low, closes[-2]]

        # Should have inside weeks at this point
        # make sure we have a full 60 min bar before executing below
        
        # make sure we're trading above the daily open
        if current_prices[sec] > today_open[sec][0]:
            # make sure we're trading 
            if current_prices[sec] > context.output['monthly_high'][sec]:
                # we've broken out of the week now test the hour
                if sec in context.hourly_data:
                    print(context.hourly_data[sec])

def assess_daily_gamma(context, sec, open_orders, current_prices):
    """
    Assess daily gamma
    """
    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    have_short_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount < 0
    have_long_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount > 0
    no_pos_or_orders = sec not in open_orders and ~(
        have_long_pos or have_short_pos)
    has_gamma = (context.output['daily_classifier'][sec] == BAR_TYPE['gamma'] or
                 context.output['daily_classifier'][sec] == BAR_TYPE['gamma_alpha'] or
                 context.output['daily_classifier'][sec] == BAR_TYPE['gamma_beta'])
    has_gamma_daily_breakout_long = current_prices[sec] > context.output['daily_high'][sec]
    has_gamma_daily_breakout_short = current_prices[sec] < context.output['daily_low'][sec]
    has_traded_today = sec.sid not in context.position_logs
    if no_pos_or_orders and has_traded_today and has_gamma:
        if has_gamma_daily_breakout_long:
            context.gamma_daily_breakout_long = 1  # current_prices[sec]
            if context.trade_gamma_long:
                insert_in_log(context, sec, ',' + str(exchange_time)
                              + ',gamma long,'
                              + sec.symbol + ','
                              + str(context.output['daily_high'][sec]) + ','
                              + str(current_prices[sec]) + ','
                              + str(context.output['daily_low'][sec]) + '\r')
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['daily_low'][sec]
                # order_target(sec, 1)
                order_target_percent(sec, 1)
        if has_gamma_daily_breakout_short:
            context.gamma_daily_breakout_short = -1  # current_prices[sec]
            if context.trade_gamma_short:
                insert_in_log(context, sec, ',' + str(exchange_time)
                              + ',gamma short,'
                              + sec.symbol + ','
                              + str(context.output['daily_low'][sec]) + ','
                              + str(current_prices[sec]) + ','
                              + str(context.output['daily_high'][sec]) + '\r')
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['daily_high'][sec]
                # order_target(sec, 1)
                order_target_percent(sec, -1)
    context.gamma_daily_bar = 0.5 if (
        ~has_gamma_daily_breakout_long or ~has_gamma_daily_breakout_short) and has_gamma else 0

    ##### LOOK TO SEE IF WE HAVE A POSITION AND NEED TO ALTER THE STOP LOSS #####
    ##### THIS WOULD OCCUR IF WE ARE LONG AND RAN INTO ANOTHER ALPHA BAR #####
    if (have_long_pos or have_short_pos) and has_gamma:
        if has_gamma_daily_breakout_long and context.trade_gamma_long:
            context.positions_stop_loss[sec.sid] = context.output['daily_low'][sec]
        elif has_gamma_daily_breakout_short and context.trade_gamma_short:
            context.positions_stop_loss[sec.sid] = context.output['daily_high'][sec]


def assess_daily_alpha(context, sec, open_orders, current_prices, available_allocation):
    """
    Assess daily alpha
    """
    to_return = 0
    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    have_short_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount < 0
    have_long_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount > 0
    #no_pos_or_orders = sec not in open_orders and not (have_long_pos or have_short_pos)
    has_alpha = context.output['daily_classifier'][sec] == BAR_TYPE['alpha']

    has_alpha_daily_breakout = context.output['daily_high'][sec] < current_prices[sec]
    not_traded_today = sec.sid not in context.position_logs
    if not_traded_today and has_alpha:
        if has_alpha_daily_breakout:
            context.alpha_daily_breakout = 1
            to_return = 1
            if available_allocation != 0:
                insert_in_log(context, sec, ',' + str(exchange_time)
                              + ',alpha daily,'
                              + sec.symbol + ','
                              + str(context.output['daily_high'][sec]) + ','
                              + str(current_prices[sec]) + ','
                              + str(context.output['daily_low'][sec]) + '\r')
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['daily_low'][sec]
                # order_target(sec, 1)
                to_allocate = min(available_allocation, 0.5)
                order_percent(sec, to_allocate)
    context.alpha_daily_bar = 0.5 if has_alpha else 0

    ##### LOOK TO SEE IF WE HAVE A POSITION AND NEED TO ALTER THE STOP LOSS #####
    ##### THIS WOULD OCCUR IF WE ARE LONG AND RAN INTO ANOTHER ALPHA BAR #####
    if (have_long_pos or have_short_pos) and has_alpha and has_alpha_daily_breakout:
        context.positions_stop_loss[sec.sid] = context.output['daily_low'][sec]

    return to_return


def assess_weekly_alpha(context, sec, open_orders, current_prices, available_allocation):
    """
    Assess weekly alpha
    """
    to_return = 0
    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    have_short_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount < 0
    have_long_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount > 0
    no_pos_or_orders = sec not in open_orders and not (
        have_long_pos or have_short_pos)
    has_alpha_weekly = context.output['weekly_classifier'][sec] == BAR_TYPE['alpha']
    has_alpha_weekly_breakout = context.output['weekly_high'][sec] < current_prices[sec]
    not_traded_today = sec.sid not in context.position_logs
    if not_traded_today and has_alpha_weekly:
        if has_alpha_weekly_breakout:
            context.alpha_weekly_breakout = 2.0
            to_return = 1
            if available_allocation != 0:
                insert_in_log(context, sec, ',' + str(exchange_time)
                              + ',alpha weekly,'
                              + sec.symbol + ','
                              + str(context.output['weekly_high'][sec]) + ','
                              + str(current_prices[sec]) + ','
                              + str(context.output['weekly_low'][sec]) + '\r')
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['weekly_low'][sec]
                # order_target(sec, 1)
                to_allocate = min(available_allocation, 0.5)
                order_percent(sec, to_allocate)
    context.alpha_weekly_bar = 1.5 if has_alpha_weekly else 0

    ##### LOOK TO SEE IF WE HAVE A POSITION AND NEED TO ALTER THE STOP LOSS #####
    ##### THIS WOULD OCCUR IF WE ARE LONG AND RAN INTO ANOTHER ALPHA BAR #####
    if (have_long_pos or have_short_pos) and has_alpha_weekly and has_alpha_weekly_breakout:
        context.positions_stop_loss[sec.sid] = context.output['weekly_low'][sec]
    return to_return


def assess_daily_beta(context, sec, open_orders, current_prices):
    """
    Assess daily beta
    """
    exchange_time = get_datetime().astimezone(timezone('US/Eastern'))
    have_short_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount < 0
    have_long_pos = sec in context.portfolio.positions and context.portfolio.positions[
        sec].amount > 0
    no_pos_or_orders = sec not in open_orders and ~(
        have_long_pos or have_short_pos)
    has_beta = context.output['daily_classifier'][sec] == BAR_TYPE['beta']
    has_beta_daily_breakout = has_beta and current_prices[sec] < context.output['daily_low'][sec]
    has_traded_today = sec.sid not in context.position_logs
    if no_pos_or_orders and has_traded_today and has_beta:
        if has_beta_daily_breakout:
            context.beta_daily_breakout = -1
            if context.trade_beta:
                insert_in_log(context, sec, ',' + str(exchange_time)
                              + ',beta,'
                              + sec.symbol + ','
                              + str(context.output['daily_high'][sec]) + ','
                              + str(current_prices[sec]) + ','
                              + str(context.output['daily_low'][sec]) + '\r')
                context.positions_max_gain[sec.sid] = 0
                context.positions_stop_loss[sec.sid] = context.output['daily_high'][sec]
                # order_target(sec, -1)
                order_target_percent(sec, -1)
    context.beta_daily_bar = -0.5 if ~has_beta_daily_breakout and has_beta else 0
    ##### LOOK TO SEE IF WE HAVE A POSITION AND NEED TO ALTER THE STOP LOSS #####
    ##### THIS WOULD OCCUR IF WE ARE LONG AND RAN INTO ANOTHER ALPHA BAR #####
    if (have_long_pos or have_short_pos) and has_beta and has_beta_daily_breakout and context.trade_beta:
        context.positions_stop_loss[sec.sid] = context.output['daily_high'][sec]


def insert_in_log(context, sec, msg):
    """
    Insert into log
    """
    if sec.sid not in context.position_logs:
        context.position_logs[sec.sid] = []

    context.position_logs[sec.sid].append(msg)


def log_trade_info(context, data):
    """
    Log trade information
    """
    if context.position_logs:
        main_log = '\n'
        for log in context.position_logs:
            for log_msg in context.position_logs[log]:
                main_log += log_msg
        print(main_log)
        context.position_logs = {}
    if context.trade_alpha:
        record(
            alpha_daily_bar=context.alpha_daily_bar,
            alpha_daily_breakout=context.alpha_daily_breakout,
            alpha_weekly_bar=context.alpha_weekly_bar,
            alpha_weekly_breakout=context.alpha_weekly_breakout
        )
    elif context.trade_beta:
        record(
            beta_daily_bar=context.beta_daily_bar,
            beta_daily_breakout=context.beta_daily_breakout
        )
    elif context.trade_gamma_long or context.trade_gamma_short:
        record(
            gamma_daily_breakout_long=context.gamma_daily_breakout_long,
            gamma_daily_breakout_short=context.gamma_daily_breakout_short,
            gamma_daily_bar=context.gamma_daily_bar
        )
    context.gamma_daily_breakout_long = 0
    context.gamma_daily_breakout_short = 0
    context.gamma_daily_bar = 0
    context.alpha_daily_bar = 0
    context.alpha_daily_breakout = 0
    context.alpha_weekly_bar = 0
    context.alpha_weekly_breakout = 0
    context.beta_daily_bar = 0
    context.beta_daily_breakout = 0


class DailyClassifier(CustomFactor):
    """
    Classifiy daily bars
    """
    window_length = 2

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Do classification
        """
        r_alpha = (high[-1] - low[-1]) / ALPHA_DIVISOR
        alpha_z = high[-1] - r_alpha

        r_beta = (high[-1] - low[-1]) / BETA_DIVISOR
        beta_z = low[-1] + r_beta

        is_alpha = (open[-1] > alpha_z) & (close[-1] >
                                           alpha_z)  # & (close[-1] > open[-1])
        is_beta = (open[-1] < beta_z) & (close[-1] <
                                         beta_z)  # & (close[-1] < open[-1])
        is_gamma = (high[-1] < high[0]) & (low[-1] > low[0])
        is_delta = (high[-1] > high[0]) & (low[-1] < low[0])

        bar_types = [0] * len(open[-1])
        bar_types = (is_alpha << 1) + bar_types
        bar_types = (is_beta << 2) + bar_types
        bar_types = (is_gamma << 3) + bar_types
        bar_types = (is_delta << 4) + bar_types
        out[:] = bar_types


class WeeklyClassifier(CustomFactor):
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
        for num in range(-WeeklyClassifier.window_length, 0)[::-1]:
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
                if prev_day == 0 and new_day == 4:
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
        is_gamma = (prev_week_high < current_week_high) & (
            prev_week_low > current_week_low)
        is_delta = (prev_week_high > current_week_high) & (
            prev_week_low < current_week_low)

        bar_types = [0] * len(open[-1])
        bar_types = (is_alpha << 1) + bar_types
        bar_types = (is_beta << 2) + bar_types
        bar_types = (is_gamma << 3) + bar_types
        bar_types = (is_delta << 4) + bar_types
        out[:] = bar_types


class WeeklyHigh(CustomFactor):
    """
    Get the high for the week
    """
    window_length = 14

    def compute(self, today, asset_ids, out, high):
        """
            Get the high for the week
        """
        today_day = today.weekday()
        current_end_week_idx = today_day
        current_start_week_idx = 4 + today_day
        current_week_high = high[current_end_week_idx:current_start_week_idx, :].max(
            axis=0)
      #  current_week_low = low[current_end_week_idx:current_start_week_idx, :].min(axis=0)
        out[:] = current_week_high


class WeeklyLow(CustomFactor):
    """
    Get the low for the week
    """
    window_length = 14

    def compute(self, today, asset_ids, out, low):
        """
        Get the low for the week
        """
        today_day = today.weekday()
        current_end_week_idx = today_day
        current_start_week_idx = 4 + today_day
      #  current_week_high = high[current_end_week_idx:current_start_week_idx, :].max(axis=0)
        current_week_low = low[current_end_week_idx:current_start_week_idx, :].min(
            axis=0)
        out[:] = current_week_low


class MonthlyClassifier(CustomFactor):
    """
    Classifiy monthly bars
    """
    window_length = 92

    def compute(self, today, asset_ids, out, open, high, low, close):
        """
            Do monthly classification
        """

     #   day_of_month = today.day
      #  if day_of_month != 1:
      #      return

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

        while idx > -MonthlyClassifier.window_length:
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
        out[:] = bar_types

class CurrentInsideMonthClassifier(CustomFactor):
    """
    Determine if current month is trading within prev months range
    """
    window_length = 61

    def compute(self, today, asset_ids, out, high, low):
        """
            Determine if current month is trading within prev months range
        """

     #   day_of_month = today.day
      #  if day_of_month != 1:
      #      return

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

        while idx > -MonthlyClassifier.window_length:
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
        out[:] = start_month_high > current_month_high | start_month_low < current_month_low


class MonthlyHigh(CustomFactor):
    """
    Get the high for the week
    """
    window_length = 32

    def compute(self, today, asset_ids, out, high):
        """
            Get the high for the week
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        prev_month = current_month - 1 if current_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        while idx > -MonthlyClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx
            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1

        if current_end_month_idx == -1:
            current_month_high = high[current_start_month_idx:, :].max(
                axis=0)
            # current_month_low = low[current_start_month_idx:, :].min(axis=0)
        else:
            current_month_high = high[current_start_month_idx:current_end_month_idx + 1, :].max(
                axis=0)

           # current_month_low = low[current_start_month_idx:current_end_month_idx + 1, :].min(axis=0)
        out[:] = current_month_high


class MonthlyLow(CustomFactor):
    """
    Get the low for the month
    """
    window_length = 32

    def compute(self, today, asset_ids, out, low):
        """
            Get the low for the month
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        prev_month = current_month - 1 if current_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        while idx > -MonthlyClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx
            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1

        if current_end_month_idx == -1:
           # current_month_high = high[current_start_month_idx:, :].max(axis=0)
            current_month_low = low[current_start_month_idx:, :].min(axis=0)
        else:
            # current_month_high = high[current_start_month_idx:current_end_month_idx + 1, :].max(axis=0)
            current_month_low = low[current_start_month_idx:
                                    current_end_month_idx + 1, :].min(axis=0)
        out[:] = current_month_low

class MonthlyCurrentLow(CustomFactor):
    """
    Get the low for the current incomplete monthly bar
    """
    window_length = 32

    def compute(self, today, asset_ids, out, low):
        """
            Compute the low for the current incomplete monthly bar
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        prev_month = current_month - 1 if current_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        while idx > -MonthlyClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx
            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1


        # current_month_high = high[current_end_month_idx:, :].max(axis=0)
        start_month_low = low[current_end_month_idx:, :].min(axis=0)

        out[:] = start_month_low

class MonthlyCurrentHigh(CustomFactor):
    """
    Get the low for the current incomplete monthly bar
    """
    window_length = 32

    def compute(self, today, asset_ids, out, high):
        """
            Compute the low for the current incomplete monthly bar
        """
        start_month = today.month
        current_month = start_month - 1 if start_month - 1 > 0 else 12
        prev_month = current_month - 1 if current_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        while idx > -MonthlyClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx
            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1

            date_idx = date_idx - 1
            month_idx = date_idx.month
            idx = idx - 1


         start_month_high = high[current_end_month_idx:, :].max(axis=0)
        #start_month_low = low[current_end_month_idx:, :].min(axis=0)

        out[:] = start_month_high


class VolumeFilter(CustomFilter):
    """
    Filter by volume
    """

    def compute(self, today, asset_ids, out, volume):
        """
        Compare volume
        """
        out[:] = volume[0] > 200000