class MonthlyOutsideFilter(CustomFilter):
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

