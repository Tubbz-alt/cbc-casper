"""The view module ... """

class AbstractView(object):
    """A set of seen messages. For performance, also stores a dict of most recent messages."""
    def __init__(self, messages=None):
        # now for some assignment...
        if messages is None:
            messages = set()

        self.add_messages(messages)

        self.justified_messages = dict()            # message hash => message
        self.pending_messages = dict()              # message hash => message

        self.missing_message_dependencies = dict()  # message hash => set(message hashes)
        self.dependents_of_message = dict()         # message hash => list(message hashes)

        self.latest_messages = dict()               # validator => message

    def missing_messages_in_justification(self, message):
        """Returns the set of not seen messages hashes from the justification of a message"""
        return {
            message_hash for message_hash in message.justification.values()
            if message_hash not in self.justified_messages
        }

    def estimate(self):
        '''Must be defined in child class.
        Returns estimate based on current messages in the view'''
        raise NotImplementedError

    def update_safe_estimates(self, validator_set):
        '''Must be defined in child class.'''
        raise NotImplementedError

    def add_messages(self, showed_messages):
        """Adds a set of newly received messages to pending or justified"""
        for message in showed_messages:
            if message.hash in self.pending_messages or message.hash in self.justified_messages:
                continue

            missing_message_hashes = self.missing_messages_in_justification(message)
            if not any(missing_message_hashes):
                self.mark_message_as_fully_received(message)
                self.resolve_waiting_messages(message)
                continue

            self.pending_messages[message.hash] = message
            self._track_missing_messages(message, missing_message_hashes)

    def resolve_waiting_messages(self, message):
        """Given a new message, resolve all messages that are waiting for it to be justified"""
        if message.hash not in self.dependents_of_message:
            return

        for dependent_hash in self.dependents_of_message[message.hash]:
            # sanity check!
            assert message.hash in self.missing_message_dependencies[dependent_hash]

            self.missing_message_dependencies[dependent_hash].remove(message.hash)

            if not any(self.missing_message_dependencies[dependent_hash]):
                new_message = self.pending_messages[dependent_hash]
                self.resolve_waiting_messages(new_message)

                self.mark_message_as_fully_received(new_message)

        del self.dependents_of_message[message.hash]

    def mark_message_as_fully_received(self, message):
        """Must be defined in child class
        Adds a message with all messages in justification received to view"""
        self._add_to_latest_messages(message)
        self._add_justified_remove_pending(message)

    def _add_to_latest_messages(self, message):
        # update views most recently seen messages
        if message.sender not in self.latest_messages:
            self.latest_messages[message.sender] = message
        elif self.latest_messages[message.sender].sequence_number < message.sequence_number:
            self.latest_messages[message.sender] = message

    def _add_justified_remove_pending(self, message):
        self.justified_messages[message.hash] = message
        if message.hash in self.missing_message_dependencies:
            del self.missing_message_dependencies[message.hash]
        if message.hash in self.pending_messages:
            del self.pending_messages[message.hash]

    def _track_missing_messages(self, message, missing_message_hashes):
        for missing_message_hash in missing_message_hashes:
            if missing_message_hash not in self.dependents_of_message:
                self.dependents_of_message[missing_message_hash] = []

            self.dependents_of_message[missing_message_hash].append(message.hash)
            self.missing_message_dependencies[message.hash] = missing_message_hashes
