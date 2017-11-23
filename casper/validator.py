"""The validator module contains the Validator class, which creates/sends/recieves messages """
import numbers
from casper.blockchain.blockchain_protocol import BlockchainProtocol

class Validator(object):
    """A validator has a view from which it generates new messages and detects finalized blocks."""
    def __init__(self, name, weight, protocol=BlockchainProtocol, validator_set=None):
        if name is None:
            raise ValueError("Validator name must be defined.")
        if not isinstance(weight, numbers.Number):
            raise ValueError("Validator weight must a number.")
        if weight < 0:
            raise ValueError("Validator weight cannot be less than 0.")

        self.name = name
        self.weight = weight
        self.view = protocol.View(set())
        self.validator_set = validator_set
        self.protocol = protocol

    def receive_messages(self, messages):
        """Allows the validator to receive protocol messages."""
        self.view.add_messages(messages)

    def estimate(self):
        """The estimator function returns the set of max weight estimates.
        This may not be a single-element set because the validator may have an empty view."""
        return self.view.estimate()

    def my_latest_message(self):
        """This function returns the validator's latest message."""
        if self in self.view.latest_messages:
            return self.view.latest_messages[self]
        return None

    def update_safe_estimates(self):
        """The validator checks estimate safety on some estimate with some safety oracle."""
        self.view.update_safe_estimates(self.validator_set)

    def make_new_message(self):
        """This function produces a new latest message for the validator.
        It updates the validator's latest message, estimate, view, and latest observed messages."""
        estimate = self.estimate()
        justification = self.justification()
        sequence_number = self.next_sequence_number()
        display_height = self.next_display_height()

        new_message = self.protocol.Message(
            estimate,
            justification,
            self,
            sequence_number,
            display_height
        )
        self.view.add_messages(set([new_message]))
        assert new_message.hash in self.view.justified_messages  # sanity check

        return new_message

    def next_sequence_number(self):
        """Returns the sequence number for the next message from a validator"""
        last_message = self.my_latest_message()

        if last_message:
            return last_message.sequence_number + 1
        return 0

    def next_display_height(self):
        """Returns the display height for a message created in this view"""
        if not any(self.view.latest_messages):
            return 0

        max_height = max(
            self.view.latest_messages[validator].display_height
            for validator in self.view.latest_messages
        )
        return max_height + 1

    def justification(self):
        """Returns the headers of latest message seen from other validators."""
        latest_message_headers = dict()
        for validator in self.view.latest_messages:
            latest_message_headers[validator] = self.view.latest_messages[validator].hash
        return latest_message_headers
