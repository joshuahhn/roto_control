"""Issue #8 experiment only. No imports from, or hooks into, the production host."""
import math


class Takeover:
    """Fake-clock ownership policy; the caller owns scheduling and accepted writes.

    Inputs are target units, after MIDI/session/echo validation. One timer slot is
    represented by (epoch, revision, deadline); replacing it cancels its predecessor.
    """

    def __init__(self, timeout=2.0, minimum=0.0, maximum=1.0, integer=False):
        if not all(math.isfinite(x) for x in (timeout, minimum, maximum)):
            raise ValueError('Finite timeout and range required')
        if timeout <= 0 or minimum >= maximum:
            raise ValueError('Positive timeout and increasing range required')
        if integer and (int(minimum) != minimum or int(maximum) != maximum):
            raise ValueError('Integer bounds required')
        self.timeout, self.minimum, self.maximum = timeout, minimum, maximum
        self.integer = integer
        self.now = 0.0
        self.epoch = self.revision = 0
        self.active = True
        self.owner = 'unavailable'
        self.latest = self.effective = None
        self.touched = False
        self.timer = None

    def quantize(self, value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Finite value required')
        value = min(self.maximum, max(self.minimum, value))
        return round(value) if self.integer else value

    def cancel(self):
        self.revision += 1
        self.timer = None

    def arm(self):
        self.cancel()
        if self.active and self.owner == 'manual' and not self.touched:
            self.timer = (self.epoch, self.revision, self.now + self.timeout)

    def source(self, value, epoch=None):
        if not self.active or epoch is not None and epoch != self.epoch:
            return
        try:
            self.latest = self.quantize(value)
        except (ValueError, TypeError):
            self.latest = None
            if self.owner != 'manual':
                self.owner = 'unavailable'
            return
        if self.owner != 'manual':
            self.owner, self.effective = 'upstream', self.latest
        elif not self.touched and self.timer is None:
            # Idle already elapsed while source was absent. Use this fresh sample.
            self.owner, self.effective = 'upstream', self.latest

    def movement(self, value, epoch=None):
        if not self.active or epoch is not None and epoch != self.epoch:
            return
        self.effective = self.quantize(value)
        self.owner = 'manual'
        self.arm()

    def feedback(self):
        """A publication/ACK is not an ownership event. No motor I/O in this model."""
        return self.effective

    def touch(self, held, epoch=None):
        if not self.active or epoch is not None and epoch != self.epoch:
            return
        if bool(held) == self.touched:
            return
        self.touched = bool(held)
        if held:
            self.cancel()
        elif self.owner == 'manual':
            self.arm()

    def advance(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Clock must advance by finite nonnegative seconds')
        self.now += seconds
        self.fire(self.timer)

    def fire(self, token):
        if (token is None or token != self.timer or not self.active
                or self.touched or self.now < token[2]):
            return
        self.cancel()
        if self.latest is not None:
            self.owner, self.effective = 'upstream', self.latest

    def fence(self, active=False):
        """Context/session/LEARN transition or detach: discard old source and gesture."""
        self.epoch += 1
        self.cancel()
        self.active = active
        self.owner = 'unavailable' if active else 'disabled'
        self.latest = None
        self.touched = False

    def snapshot(self):
        return dict(now=self.now, owner=self.owner, latest=self.latest,
                    effective=self.effective, touched=self.touched, active=self.active,
                    epoch=self.epoch, timer=self.timer)


def verify_policy():
    """Scripted acceptance of the candidate policy, not hardware acceptance."""
    p = Takeover()
    p.source(.2)
    assert p.effective == .2 and p.owner == 'upstream'
    p.touch(True)
    p.movement(.8)
    p.source(.4)
    p.advance(10)
    assert p.effective == .8 and p.latest == .4 and p.timer is None
    p.touch(False)
    old = p.timer
    p.advance(1)
    before_feedback = p.snapshot()
    assert p.feedback() == .8 and p.snapshot() == before_feedback
    p.touch(False)
    assert p.snapshot() == before_feedback
    p.movement(.7)
    p.source(.6)
    p.advance(1)
    p.fire(old)
    assert p.owner == 'manual' and p.effective == .7
    p.advance(1)
    assert p.owner == 'upstream' and p.effective == .6
    p.movement(.9)
    p.source(float('nan'))
    p.advance(2)
    assert p.owner == 'manual' and p.latest is None and p.effective == .9
    p.source(.3)
    assert p.owner == 'upstream' and p.effective == .3
    p.movement(.7)
    old, epoch = p.timer, p.epoch
    p.fence(active=True)
    p.source(.1)
    p.movement(.99, epoch)
    p.source(.99, epoch)
    p.touch(True, epoch)
    p.advance(10)
    p.fire(old)
    assert p.effective == .1 and p.owner == 'upstream' and not p.touched
    p.fence()
    p.source(.8)
    p.movement(.8)
    assert p.effective == .1 and p.owner == 'disabled'
    q = Takeover(minimum=0, maximum=3, integer=True)
    q.source(8)
    assert q.effective == 3
    q.movement(1.6)
    assert q.effective == 2
    q.source(float('inf'))
    assert q.latest is None
    return dict(upstream_tracking=True, held_touch_blocks_return=True,
                release_restarts_idle=True, latest_sample_return=True,
                renewed_movement_resets_idle=True, stale_timer_fenced=True,
                feedback_does_not_reset_idle=True,
                duplicate_release_does_not_reset_idle=True,
                stale_input_fenced=True, source_loss_holds_value=True,
                fresh_source_recovers=True, integer_quantization=True,
                nonfinite_rejected=True, timer_slots=1,
                physical_acceptance=False)


if __name__ == '__main__':
    import json
    print(json.dumps(verify_policy(), indent=2))
