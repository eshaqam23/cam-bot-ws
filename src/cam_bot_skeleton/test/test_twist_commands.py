from cam_bot_skeleton.commands import twist_motor_packet


def test_forward():
    assert twist_motor_packet(0.5, 0.0) == "70,1,70,1"


def test_backward():
    assert twist_motor_packet(-0.5, 0.0) == "70,0,70,0"


def test_left():
    assert twist_motor_packet(0.0, 1.0) == "70,0,70,1"


def test_right():
    assert twist_motor_packet(0.0, -1.0) == "70,1,70,0"


def test_stop():
    assert twist_motor_packet(0.0, 0.0) == "0,1,0,1"


def test_forward_left_arc():
    assert twist_motor_packet(0.5, 1.0) == "0,1,70,1"