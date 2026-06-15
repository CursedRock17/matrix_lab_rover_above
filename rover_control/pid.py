class PID:
    def __init__(self, kp, ki, kd, output_limit):
        # Controller gains: proportional, integral, and derivative
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.reset()

    def reset(self):
        # Clear the stored state so the controller starts fresh
        self._integral = 0.0
        self._last_error = None

    def update(self, error, dt):
        # Proportional term reacts to the error we have right now
        p = self.kp * error

        # Integral term accumulates leftover error over time
        self._integral += error * dt
        i = self.ki * self._integral

        # Derivative term damps fast changes in the error
        d = 0.0
        if self._last_error is not None and dt > 0:
            d = self.kd * (error - self._last_error) / dt
        self._last_error = error

        # Combine the three terms into one output command
        output = p + i + d

        # Clamp the output and undo the integral step when saturated (anti-windup)
        if output > self.output_limit:
            output = self.output_limit
            self._integral -= error * dt
        elif output < -self.output_limit:
            output = -self.output_limit
            self._integral -= error * dt
        return output
