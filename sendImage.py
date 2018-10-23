def sendImage():
    device.update_sensor_data()
    # Process network events.
    client.loop()

    # Wait if backoff is required.
    if should_backoff:
        # If backoff time is too large, give up.
        if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
            print('Exceeded maximum backoff time. Giving up.')
            break

        # Otherwise, wait and connect again.
        delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
        print('Waiting for {} before reconnecting.'.format(delay))
        time.sleep(delay)
        minimum_backoff_time *= 2
        client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    with open('cat.jpg', 'rb') as imageFile:
        f = imageFile.read()
        b = bytearray(f)


    # [START iot_mqtt_jwt_refresh]
    seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
    if seconds_since_issue > 60 * jwt_exp_mins:
        print('Refreshing token after {}s').format(seconds_since_issue)
        jwt_iat = datetime.datetime.utcnow()
        client = device.get_client(
            args.project_id, args.cloud_region,
            args.registry_id, args.device_id, args.private_key_file,
            args.algorithm, args.ca_certs, args.mqtt_bridge_hostname,
            args.mqtt_bridge_port)
    # [END iot_mqtt_jwt_refresh]

    # Publish "payload" to the MQTT topic. qos=1 means at least once
    # delivery. Cloud IoT Core also supports qos=0 for at most once
    # delivery.

    # Publish image payload to imgtopic
    print('Publishing image payload as bytes', payload)
    client.publish(mqtt_img_topic, b, qos=1)