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

        while idx > -MonthlyCurrentLow.window_length:
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

