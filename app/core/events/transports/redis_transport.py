"""Ported unchanged from D:\\OMR_System\\app\\core\\events\\transports\\redis_transport.py."""

import json
import threading
import redis

from typing import Callable, Optional, Any
from app.core.events.transports.base_transport import BaseTransport
from app.core.logging.logger import logger

class RedisTransport(BaseTransport):
    def __init__(
        self,
        broker_url: str,
        is_subscriber: bool = False,
        local_dispatch_callback: Optional[Callable[[str, Any], None]] = None
    ):
        self.r = redis.from_url(
            broker_url,
            socket_timeout=None,
            socket_connect_timeout=30,
            retry_on_timeout=True
        )
        self.channel = "ocr_events"
        self.is_subscriber = is_subscriber
        self.local_dispatch_callback = local_dispatch_callback

        if self.is_subscriber and self.local_dispatch_callback:
            self.pubsub = self.r.pubsub(ignore_subscribe_messages=True)
            self.pubsub.subscribe(self.channel)
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            logger.info("RedisTransport SUBSCRIBER started.")
        else:
            logger.info("RedisTransport PUBLISHER started.")

    def _listen(self):

        while True:

            try:

                message = self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if not message:
                    continue

                data = json.loads(
                    message["data"]
                )

                event_name = data.get(
                    "event_name"
                )

                payload = data.get(
                    "payload"
                )

                if (
                    event_name and
                    payload is not None
                ):
                    self.local_dispatch_callback(
                        event_name,
                        payload
                    )

            except Exception as e:

                logger.error(
                    f"Redis subscriber error: {e}"
                )
    def send(self, event_name: str, payload: Any):
        # We publish everything we receive to Redis.
        # If we are the subscriber, we don't need to publish back (unless we want to).
        # We can just publish blindly.

        logger.info(
            f"[REDIS PUB] {event_name}"
        )
        try:
            self.r.publish(self.channel, json.dumps({
                "event_name": event_name,
                "payload": payload
            }))
        except Exception as e:
            logger.error(f"RedisTransport failed to publish: {e}")
