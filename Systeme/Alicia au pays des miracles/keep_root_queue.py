#!/usr/bin/env python3
"""Ensure that the durable RabbitMQ queue 'root' contains a ready payload."""

import sys

import pika

QUEUE = "root"
PAYLOAD = b"IsItARootPasswordISee???"


def main() -> int:
    connection = None
    try:
        credentials = pika.PlainCredentials("guest", "guest")
        parameters = pika.ConnectionParameters(
            host="127.0.0.1",
            port=5672,
            virtual_host="/",
            credentials=credentials,
            connection_attempts=1,
            socket_timeout=3,
            stack_timeout=5,
            blocked_connection_timeout=5,
            heartbeat=15,
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.confirm_delivery()

        # queue_declare creates the queue if it does not exist and returns
        # the number of messages currently ready for delivery.
        result = channel.queue_declare(
            queue=QUEUE,
            durable=True,
            auto_delete=False,
            arguments={},
        )

        ready_count = result.method.message_count
        if ready_count == 0:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE,
                body=PAYLOAD,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="text/plain",
                ),
                mandatory=True,
            )
            print("Payload publiée dans la file root.", flush=True)

        return 0
    except Exception as exc:  # Replayed by the shell worker after a short delay.
        print(
            f"Erreur de maintenance RabbitMQ : {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    finally:
        if connection is not None and connection.is_open:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
