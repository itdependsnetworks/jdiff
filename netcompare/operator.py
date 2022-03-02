import operator


class Operator:
    def __init__(self, referance_data, value_to_compare) -> None:
        # [{'7.7.7.7': {'peerGroup': 'EVPN-OVERLAY-SPINE', 'vrf': 'default', 'state': 'Idle'}},
        # {'10.1.0.0': {'peerGroup': 'IPv4-UNDERLAY-SPINE', 'vrf': 'default', 'state': 'Idle'}},
        # {'10.2.0.0': {'peerGroup': 'IPv4-UNDERLAY-SPINE', 'vrf': 'default', 'state': 'Idle'}},
        # {'10.64.207.255': {'peerGroup': 'IPv4-UNDERLAY-MLAG-PEER', 'vrf': 'default', 'state': 'Idle'}}]
        self.referance_data_value = list(referance_data.values())[0]
        self.value_to_compare = value_to_compare

    def _loop_through(self, call_ops):
        ops = {
            ">": operator.gt,
            "<": operator.lt,
            "is_in": operator.contains,
            "not_in": operator.contains,
            "contains": operator.contains,
            "not_contains": operator.contains,
        }

        result = list()
        for item in self.value_to_compare:
            for value in item.values():
                for evaluated_value in value.values():
                    # reverse operands (??? WHY ???) https://docs.python.org/3.8/library/operator.html#operator.contains
                    if call_ops == "is_in":
                        if ops[call_ops](self.referance_data_value, evaluated_value):
                            result.append(item)
                    elif call_ops == "not_contains":
                        if not ops[call_ops](evaluated_value, self.referance_data_value):
                            result.append(item)
                    elif call_ops == "not_in":
                        if not ops[call_ops](self.referance_data_value, evaluated_value):
                            result.append(item)
                    elif call_ops == "in_range":
                        if self.referance_data_value[0] < evaluated_value < self.referance_data_value[1]:
                            result.append(item)
                    elif call_ops == "not_range":
                        if not self.referance_data_value[0] < evaluated_value < self.referance_data_value[1]:
                            result.append(item)
                    else:
                        if ops[call_ops](evaluated_value, self.referance_data_value):
                            result.append(item)
        if result:
            return (True, result)
        else:
            return (False, result)

    def all_same(self):
        list_of_values = list()
        result = list()

        for item in self.value_to_compare:
            for value in item.values():
                # Create a list for compare valiues.
                list_of_values.append(value)

        for element in list_of_values:
            if not element == list_of_values[0]:
                result.append(False)
            else:
                result.append(True)

        if self.referance_data_value and not all(result):
            return (False, self.value_to_compare)
        elif self.referance_data_value and all(result):
            return (True, self.value_to_compare)
        elif not self.referance_data_value and not all(result):
            return (True, self.value_to_compare)
        elif not self.referance_data_value and all(result):
            return (False, self.value_to_compare)

    def contains(self):
        return self._loop_through("contains")

    def not_contains(self):
        return self._loop_through("not_contains")

    def is_gt(self):
        return self._loop_through(">")

    def is_lt(self):
        return self._loop_through("<")

    def is_in(self):
        return self._loop_through("is_in")

    def not_in(self):
        return self._loop_through("not_in")

    def in_range(self):
        return self._loop_through("in_range")

    def not_range(self):
        return self._loop_through("not_range")
