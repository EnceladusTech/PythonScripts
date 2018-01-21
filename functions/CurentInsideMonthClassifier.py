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
        two_month_ago = prev_month - 1 if prev_month - 1 > 0 else 12
        idx = -1
        date_idx = today - 1
        month_idx = date_idx.month

        current_end_month_idx = 0
        current_start_month_idx = 0

        prev_end_month_idx = 0
        prev_start_month_idx = 0

        two_month_ago_end_idx = 0
        two_month_ago_start_idx = 0

        while idx > -CurrentInsideMonthClassifier.window_length:
            if month_idx == current_month:
                if current_end_month_idx == 0:
                    current_end_month_idx = idx

            if month_idx == prev_month:
                if current_start_month_idx == 0:
                    current_start_month_idx = idx + 1
                if prev_end_month_idx == 0:
                    prev_end_month_idx = idx

            if month_idx == two_month_ago:
                if prev_start_month_idx == 0:
                    prev_start_month_idx = idx + 1
                if two_month_ago_end_idx == 0:
                    two_month_ago_end_idx = idx

            if month_idx not in [start_month, current_month, prev_month, two_month_ago]:
                if two_month_ago_start_idx == 0:
                    two_month_ago_start_idx = idx + 1

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

        # two_month_ago_high = high[two_month_ago_end_idx:, :].max(axis=0)
        # two_month_ago_low = low[two_month_ago_end_idx:, :].min(axis=0)

        is_prev_outside_month = 

        out[:] = (start_month_high > current_month_high) | (
            start_month_low < current_month_low)
