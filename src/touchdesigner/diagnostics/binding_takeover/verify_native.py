"""Run verify(td_namespace, output, policy) through live TD. Creates and removes only its own fixture.

No controller copy, MIDI connection, source reload, project save or user mappings.
Absolute file paths are runner entry points; all native parameter refs are local.
"""
from pathlib import Path
import json
import time

def verify(td, output, policy):
    Takeover, verify_policy = policy['Takeover'], policy['verify_policy']
    root, mode = td['op']('/'), td['ParMode']
    name = 'base_issue8_takeover_probe'
    if root.op(name) is not None:
        raise RuntimeError('Fixture name already occupied; refusing replacement')
    baseline = {n.id for n in root.children}
    holder = root.create(td['baseCOMP'], name)
    holder.nodeX, holder.nodeY = 1200, -600
    holder.viewer = holder.display = True
    result = dict(native_build=str(td['app'].build), project=td['project'].name,
                  project_folder=td['project'].folder, policy=verify_policy(),
                  strategies=[], physical_acceptance=False,
                  measurement_scope='synchronous source/write/eval microbenchmark; no frame or motor claim')
    try:
        source = holder.create(td['constantCHOP'], 'constant_source')
        source.viewer = True
        source.nodeX, source.nodeY = 0, 0
        source.par.const0name = 'value'
        upstream = holder.create(td['nullCHOP'], 'null_source')
        upstream.viewer = True
        upstream.nodeX, upstream.nodeY = 175, 0
        upstream.inputConnectors[0].connect(source)
        upstream.par.cooktype = 'selective'
        consumer = holder.create(td['baseCOMP'], 'base_consumer')
        consumer.viewer = consumer.display = True
        consumer.nodeX, consumer.nodeY = 400, 0
        page = consumer.appendCustomPage('Probe')
        for style in ('Float', 'Int', 'Menu'):
            append = getattr(page, 'append' + style)
            for suffix in ('driver', 'value', 'alias'):
                p = append(style + suffix)[0]
                if style == 'Menu':
                    p.menuNames = ['a', 'b', 'c']
                    p.menuLabels = ['A', 'B', 'C']
                else:
                    p.normMin, p.normMax = 0, 2 if style == 'Int' else 1
        for style in ('Float', 'Int', 'Menu'):
            driver = getattr(consumer.par, style + 'driver')
            target = getattr(consumer.par, style + 'value')
            alias = getattr(consumer.par, style + 'alias')
            alias.bindExpr = 'me.par.' + target.name
            alias.mode = mode.BIND
            original_alias = alias.bindExpr
            names = tuple(target.menuNames) if style == 'Menu' else ()

            def encode(value):
                return names[int(value)] if names else value

            def read(par):
                return names.index(par.eval()) if names else float(par.eval())

            for strategy in ('python', 'expression', 'bind'):
                target.val = encode(0)
                driver.val = encode(0)
                # Capture dormant references too. Export attachment remains unsupported.
                original = (target.mode, target.val, target.expr, target.bindExpr,
                            target.bindRange)
                if strategy == 'expression':
                    target.expr = 'me.par.' + driver.name + '.eval()'
                elif strategy == 'bind':
                    target.bindExpr = 'me.par.' + driver.name
                    target.mode = mode.BIND
                fingerprint = (target.mode, target.expr, target.bindExpr)
                p = Takeover(maximum=2 if style in ('Int', 'Menu') else 1,
                             integer=style in ('Int', 'Menu'))

                def publish():
                    driver.val = encode(p.effective)
                    if strategy == 'python':
                        target.val = encode(p.effective)
                    assert read(target) == p.effective and read(alias) == p.effective
                    assert (target.mode, target.expr, target.bindExpr) == fingerprint
                    assert alias.mode == mode.BIND and alias.bindExpr == original_alias

                def sample(value):
                    source.par.const0value = value
                    upstream.cook(force=True)
                    p.source(float(upstream['value'][0]))
                    publish()

                manual, latest = (2, 1) if p.integer else (.8, .4)
                sample(0)
                p.touch(True)
                p.movement(manual)
                publish()
                sample(latest)
                p.advance(10)
                publish()
                assert read(target) == manual
                p.touch(False)
                p.advance(2)
                publish()
                assert read(target) == p.latest
                # Supported parameter source uses its evaluated value; never writes upstream.
                p.source(read(alias))
                publish()
                target_edit = None
                if strategy == 'bind':
                    alias.val = encode(manual)
                    target_edit = dict(driver=read(driver), target=read(target),
                                       alias_mode=alias.mode.name, target_mode=target.mode.name)
                    assert read(driver) == manual
                    assert target.mode == mode.BIND and alias.mode == mode.BIND
                    # Native bidirectionality is real, but is not a takeover-policy event.
                    publish()
                started = time.perf_counter()
                for i in range(1000):
                    sample((i % 3) if p.integer else ((i % 100) / 100))
                elapsed = time.perf_counter() - started
                if p.integer:
                    sample(2)  # Verify a non-default Int/Menu choice after reload.
                # Native in-memory tox roundtrip verifies local references after reparent.
                data = consumer.saveByteArray()
                copy = holder.loadByteArray(data)
                try:
                    cp = getattr(copy.par, target.name)
                    ca = getattr(copy.par, alias.name)
                    cd = getattr(copy.par, driver.name)
                    roundtrip_value = read(cp)
                    roundtrip_exact = roundtrip_value == p.effective
                    # Record the failed bit-exact Float expectation. Reference/mode
                    # checks remain exact, and copied endpoints must agree exactly.
                    assert read(cp) == read(ca) == read(cd)
                    assert cp.mode == target.mode and ca.mode == mode.BIND
                    assert cp.expr == target.expr and cp.bindExpr == target.bindExpr
                    assert cp.style == target.style and ca.style == alias.style
                    if names:
                        assert tuple(cp.menuNames) == names
                        assert tuple(cp.menuLabels) == tuple(target.menuLabels)
                finally:
                    copy.destroy()
                # Detach only while the fingerprint is still owned. Restore all fields.
                assert (target.mode, target.expr, target.bindExpr) == fingerprint
                target.val = original[1]
                target.expr, target.bindExpr = original[2], original[3]
                target.bindRange, target.mode = original[4], original[0]
                assert target.mode == original[0] and target.val == original[1]
                assert target.expr == original[2] and target.bindExpr == original[3]
                assert alias.bindExpr == original_alias and alias.mode == mode.BIND
                result['strategies'].append(dict(style=style, strategy=strategy,
                    held_touch=True, latest_return=True, aliases_preserved=True,
                    target_mode_stable=True, native_reference_roundtrip=True,
                    detach_restored=True, bind_target_edit=target_edit,
                    roundtrip_value_exact=roundtrip_exact,
                    before_roundtrip=p.effective, after_roundtrip=roundtrip_value,
                    updates=1000, source_dispatch_eval_ms=round(elapsed * 1000, 3)))
        # Probe the reason production expression writes cannot use target.val.
        p = consumer.par.Floatvalue
        p.expr = '0.25'
        p.val = .75
        result['direct_val_replaces_expression'] = p.mode == mode.CONSTANT
        assert result['direct_val_replaces_expression']
        result['fixture_errors'] = holder.errors(recurse=True)
        assert not result['fixture_errors']
    finally:
        holder.destroy()
    result['fixture_removed'] = root.op(name) is None
    result['all_roundtrip_values_exact'] = all(
        row['roundtrip_value_exact'] for row in result['strategies'])
    result['existing_root_ids_retained'] = baseline <= {n.id for n in root.children}
    assert result['fixture_removed'] and result['existing_root_ids_retained']
    Path(output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result
