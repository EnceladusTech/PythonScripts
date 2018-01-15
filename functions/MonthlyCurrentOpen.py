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
