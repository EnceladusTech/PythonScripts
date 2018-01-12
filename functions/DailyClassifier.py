
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
