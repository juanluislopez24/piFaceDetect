import base64
import argparse
import datetime
import json
import os
import random
import ssl
import time

import jwt
import paho.mqtt.client as mqtt
import psutil

# [END iot_mqtt_includes]

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 32

# Whether to wait with exponential backoff before publishing.
should_backoff = False

# [START iot_mqtt_jwt]
def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         private_key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            An MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the private_key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
            algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)
# [END iot_mqtt_jwt]


# [START iot_mqtt_config]
def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))

class Device(object):
    """Represents the state of a single device."""

    def __init__(self):
        self.connected = False
 
    def wait_for_connection(self, timeout):
        """Wait for the device to become connected."""
        total_time = 0
        while not self.connected and total_time < timeout:
            time.sleep(1)
            total_time += 1

        if not self.connected:
            raise RuntimeError('Could not connect to MQTT bridge.')

    def on_connect(self, unused_client, unused_userdata, unused_flags, rc):
        """Callback for when a device connects."""
        print('on_connect', mqtt.connack_string(rc))

        # After a successful connect, reset backoff time and stop backing off.
        global should_backoff
        global minimum_backoff_time
        should_backoff = False
        minimum_backoff_time = 1

        self.connected = True

    def on_disconnect(self, unused_client, unused_userdata, rc):
        """Paho callback for when a device disconnects."""
        print('on_disconnect', error_str(rc))

        # Since a disconnect occurred, the next loop iteration will wait with
        # exponential backoff.
        global should_backoff
        should_backoff = True

        self.connected = False

    def on_publish(self, unused_client, unused_userdata, unused_mid):
        """Callback when the device receives a PUBACK from the MQTT bridge."""
        print('Published message acked.')

    def get_client(self,
        project_id, cloud_region, registry_id, device_id, private_key_file,
        algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port):
        """Create our MQTT client. The client_id is a unique string that identifies
        this device. For Google Cloud IoT Core, it must be in the format below."""
        client = mqtt.Client(
                client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                        .format(
                                project_id,
                                cloud_region,
                                registry_id,
                                device_id)))

        # With Google Cloud IoT Core, the username field is ignored, and the
        # password field is used to transmit a JWT to authorize the device.
        client.username_pw_set(
                username='unused',
                password=create_jwt(
                        project_id, private_key_file, algorithm))

        # Enable SSL/TLS support.
        client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
        # describes additional callbacks that Paho supports. In this example, the
        # callbacks just print to standard out.
        client.on_connect = self.on_connect
        client.on_publish = self.on_publish
        client.on_disconnect = self.on_disconnect

        # Connect to the Google MQTT bridge.
        client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

        return client




