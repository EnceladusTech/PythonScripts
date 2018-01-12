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
