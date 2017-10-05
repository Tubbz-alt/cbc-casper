import settings as s

class Model_Bet:

    def __init__(self, estimate, sender):

        # be safe. type check!...
        assert sender in s.VALIDATOR_NAMES, "...expected a validator!"

        # these are the key elements of a bet
        self.sender = sender
        self.estimate = estimate

    def __eq__(self, bet):
        if bet is None:
            return False

        assert isinstance(B, Model_Bet), "...model_bets can only equal model_bets!"

        return self.sender == bet.sender and self.estimate == bet.estimate


    @profile
    def __hash__(self):
        return hash(str(self.sender) + str(self.estimate))
