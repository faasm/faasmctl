def get_execution_time_from_message_results(result, unit="s"):
    valid_units = ["s", "ms", "us"]
    if unit not in valid_units:
        print(
            "Unrecognised time unit '{}', must be one in: {}".format(unit, valid_units)
        )
        raise RuntimeError("Unrecognised time unit!")

    # Faasm gives us the timestamps in ms
    try:
        # We have recently changed the name of the protobuf field, so support
        # both names for backwards compatibility
        start_ts = min([msg.startTimestamp for msg in result.messageResults])
    except AttributeError:
        start_ts = min([msg.timestamp for msg in result.messageResults])
    end_ts = max([msg.finishTimestamp for msg in result.messageResults])

    if unit == "s":
        return float((end_ts - start_ts) / 1e3)

    if unit == "ms":
        return float((end_ts - start_ts))

    return float((end_ts - start_ts) * 1e3)


def get_return_code_from_message_results(result):
    def get_return_code_from_message(message):
        rv = message.returnValue
        return rv

    # if len(message_results) == 1:
    # return get_return_code_from_message(message_results[0])

    rvs = set(
        [get_return_code_from_message(message) for message in result.messageResults]
    )
    assert len(rvs) == 1, "Differing return values for same app! (rv: {})".format(rvs)

    return rvs.pop()
