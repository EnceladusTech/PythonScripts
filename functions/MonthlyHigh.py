
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

        while idx > -MonthlyHigh.window_length:
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

