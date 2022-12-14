from cs_demand_model.rpc.state import state_property


class State:
    def __init__(self):
        self.first_value = None
        self.calc_count = 0

    @state_property
    def second_value(self, first_value):
        return first_value + 1

    @state_property
    def third_value(self, second_value):
        return second_value + 1

    @state_property(cache=5)
    def fourth_value(self, second_value, third_value):
        self.calc_count += 1
        return third_value * second_value


class Default:
    def __init__(self, value):
        self.__initial = value
        self.__value = None

    def set_value(self, value):
        self.__value = value

    @property
    def value(self):
        return self.__value or self.__initial


def test_state():
    state = State()

    assert state.first_value is None
    assert state.second_value is None
    assert state.third_value is None
    assert state.fourth_value is None
    assert state.calc_count == 0

    state.first_value = 1
    assert state.first_value == 1
    assert state.second_value == 2
    assert state.third_value == 3
    assert state.calc_count == 0
    assert state.fourth_value == 6
    assert state.calc_count == 1

    state.first_value = None
    assert state.fourth_value is None
    assert state.calc_count == 1

    state.first_value = 2
    assert state.fourth_value == 12
    assert state.calc_count == 2

    state.first_value = 1
    assert state.fourth_value == 6
    assert state.calc_count == 2  # cached
