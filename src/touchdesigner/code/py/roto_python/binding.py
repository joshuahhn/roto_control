"""Target-unit conversion and two adapters; no TD or MIDI dependency."""
import math


def parameter_chain(parameter):
    """Writable Par references, ending at a constant-mode Par master.

    Never replace an expression/export master with a constant value. Non-Par
    masters are intentionally unsupported until their write semantics are tested.
    """
    chain, seen = [], set()
    current = parameter
    while current is not None:
        if not hasattr(current, 'mode') or not hasattr(current, 'owner'):
            raise ValueError("BIND requires a writable parameter master")
        key = (getattr(current.owner, 'path', None), getattr(current, 'name', id(current)))
        if key in seen:
            raise ValueError("Cyclic parameter BIND")
        seen.add(key)
        if not current.owner.valid or current.readOnly:
            raise ValueError("Target or bind master deleted/readonly")
        chain.append(current)
        if current.mode.name == 'CONSTANT':
            return chain
        if current.mode.name != 'BIND':
            raise ValueError("Target or bind master must use CONSTANT or BIND mode")
        master = getattr(current, 'bindMaster', None)
        if master is None:
            raise ValueError("Missing parameter bind master")
        if getattr(master, 'style', None) != getattr(current, 'style', None):
            raise ValueError("Parameter and bind master styles must match")
        current = master
    raise ValueError("Missing parameter bind master")


def parameter_value(parameter):
    if getattr(parameter, 'style', '') == 'Menu':
        names = list(parameter.menuNames)
        value = parameter.eval()
        if value not in names:
            raise ValueError('Menu value is not a current option')
        return names.index(value)
    return parameter.eval()


class Binding:
    def __init__(self, id, label, minimum, maximum, value, *, integer=False,
                 parameter=None, on_change=None):
        if not isinstance(id, str) or not id.strip():
            raise ValueError("A nonempty stable target id is required")
        if not isinstance(label, str) or not label.strip():
            raise ValueError("A nonempty label is required")
        self.id, self.label = id, label
        self.minimum, self.maximum = float(minimum), float(maximum)
        if (not math.isfinite(self.minimum) or not math.isfinite(self.maximum)
                or self.minimum >= self.maximum
                or not math.isfinite(self.maximum - self.minimum)):
            raise ValueError("Limits must be finite with minimum < maximum")
        if integer and (not self.minimum.is_integer() or not self.maximum.is_integer()):
            raise ValueError("Integer target limits must be integers")
        if on_change is not None and not callable(on_change):
            raise TypeError("on_change must be callable")
        self.menu_names = tuple(parameter.menuNames) if getattr(parameter, 'style', '') == 'Menu' else ()
        self.menu_labels = tuple(parameter.menuLabels) if self.menu_names else ()
        if self.menu_names:
            if (not 2 <= len(self.menu_names) <= 24 or len(set(self.menu_names)) != len(self.menu_names)
                    or len(self.menu_labels) != len(self.menu_names)):
                raise ValueError('Menu needs 2..24 unique names and matching labels')
            if minimum != 0 or maximum != len(self.menu_names)-1:
                raise ValueError('Menu range must include all option indices')
            integer = True
        self.integer, self.parameter, self.on_change = integer, parameter, on_change
        self.value = self.clamp(value)
        self.expected = None
        self.valid = True

    @property
    def signature(self):
        return (self.minimum, self.maximum, self.integer, self.menu_names, self.menu_labels)

    @property
    def wire_identity(self):
        # Include value semantics so old mappings cannot change a new range.
        identity = f"{self.id}:{self.minimum!r}:{self.maximum!r}:{int(self.integer)}"
        return identity + repr((self.menu_names, self.menu_labels)) if self.menu_names else identity

    def clamp(self, value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Value must be finite")
        value = min(self.maximum, max(self.minimum, value))
        return round(value) if self.integer else value

    def normalized(self, value):
        return (self.clamp(value) - self.minimum) / (self.maximum - self.minimum)

    def from_normalized(self, value):
        return self.clamp(self.minimum + float(value) * (self.maximum - self.minimum))

    def check_parameter(self):
        if self.parameter is None:
            return
        if self.menu_names and (tuple(self.parameter.menuNames) != self.menu_names
                                or tuple(self.parameter.menuLabels) != self.menu_labels):
            raise ValueError('Menu options changed; assign and re-learn the parameter')
        for p in parameter_chain(self.parameter):
            if getattr(p, 'style', None) in ('Float', 'Int') and (
                    p.clampMin and self.minimum < p.min or
                    p.clampMax and self.maximum > p.max):
                raise ValueError("Binding range exceeds target or bind master clamp limits")

    def write(self, value, origin):
        if not self.valid:
            raise ValueError("Binding suspended; bind again to resume")
        self.check_parameter()
        value = self.clamp(value)
        changed = value != self.value
        self.value = value
        if self.parameter is not None:
            if parameter_value(self.parameter) != value:
                self.expected = value
                self.parameter.val = self.menu_names[int(value)] if self.menu_names else value
        elif origin == "hardware" and changed and self.on_change is not None:
            self.on_change({"id": self.id, "value": value, "origin": origin})
        return value

    def format_value(self, normalized):
        value = self.from_normalized(normalized)
        if self.menu_names:
            return self.menu_labels[int(value)]
        from protocol import format_number
        return format_number(value)

    def external_changed(self, value):
        self.check_parameter()
        expected, self.expected = self.expected, None
        if self.menu_names and isinstance(value, str):
            value = self.menu_names.index(value)
        value = self.clamp(value)
        if value == expected:
            return False
        if value == self.value:
            return False
        self.value = value
        return True
