class WeeklyCurrentOpen(CustomFilter):
    """
    WeeklyCurrentOpen
    """
    window_length = 5

    def compute(self, today, asset_ids, out, open):
        """
            WeeklyCurrentOpen
        """

        today_day = today.weekday()

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


        out[:] = open[start_week_idx]
