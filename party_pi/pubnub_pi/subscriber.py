from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from pubnub_pi.pubnub_config import get_pubnub_config

class PubNubSubscriber:
    def __init__(self, channel: str, listener):
        self._channel = channel
        self._listener = listener
        self._pubnub = PubNub(get_pubnub_config())

    def start_listening(self):
        print(f"[PubNubSubscriber] Subscribing to channel: {self._channel}")
        self._pubnub.add_listener(self._listener)
        try:
            self._pubnub.subscribe().channels([self._channel]).execute()
        except PubNubException as e:
            print(f"[PubNubSubscriber] Subscription error: {e}")

    def stop_listening(self):
        print(f"[PubNubSubscriber] Unsubscribing from channel: {self._channel}")
        try:
            self._pubnub.unsubscribe().channels([self._channel]).execute()
        except PubNubException as e:
            print(f"[PubNubSubscriber] Unsubscription error: {e}")
