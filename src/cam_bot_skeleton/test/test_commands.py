from cam_bot_skeleton.commands import motor_packet


def test_forward():
    assert motor_packet("FORWARD", pwm=70) == "70,1,70,1"


def test_stop():
    assert motor_packet("STOP") == "0,1,0,1"
