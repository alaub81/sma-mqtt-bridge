"""Deterministic eCharger timestamp boundaries before changing freshness propagation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from sma_mqtt_bridge.adapters.echarger import NS, current_measurement, semp_values


class MeasurementFreshnessTests(unittest.TestCase):
    now = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)

    def stamp(self, age):
        return (self.now - timedelta(seconds=age)).isoformat()

    def test_device_age_boundaries_include_zero_and_exact_limit(self):
        for age, accepted in ((0, True), (179, True), (180, True), (180.001, False),
                              (181, False), (-0.001, False)):
            with self.subTest(age=age):
                value = current_measurement(4500, self.stamp(age), 180, self.now)
                self.assertEqual(value, 4500 if accepted else None)
        self.assertEqual(current_measurement(0, self.stamp(0), 180, self.now), 0)

    def test_timestamp_formats_and_invalid_timestamps(self):
        for stamp in ('2026-10-11T12:00:00Z', '2026-10-11T14:00:00+02:00'):
            with self.subTest(stamp=stamp):
                self.assertEqual(current_measurement(4500, stamp, 180, self.now), 4500)
        for stamp in (None, '', 'invalid', '2026-10-11T12:00:00', 123, {}):
            with self.subTest(stamp=stamp):
                self.assertIsNone(current_measurement(4500, stamp, 180, self.now))

    def test_partial_semp_reply_ages_channels_individually_and_keeps_settings(self):
        rows = (
            ('Measurement.Metering.GridMs.TotWIn.ChaSta', '4500', 179),
            ('Measurement.ChaSess.WhIn', '1500', 181),
            ('Measurement.Operation.Health', '307', 181),
            ('Measurement.Operation.EVeh.ChaStt', '200113', -1),
            ('Parameter.Chrg.ActChaMod', '4719', 86400),
        )
        body = ''.join(f'<Parameter><channelId>{channel}</channelId>'
                       f'<timestamp>{self.stamp(age)}</timestamp><value>{value}</value></Parameter>'
                       for channel, value, age in rows)
        values = semp_values(f'<Device2EM xmlns="{NS}"><Parameters>{body}</Parameters></Device2EM>',
                             180, self.now)
        self.assertEqual(values['measurements/power'], Decimal('4500'))
        for key in ('session-energy', 'health', 'vehicle-status'):
            with self.subTest(key=key):
                self.assertIsNone(values['measurements/' + key])
        self.assertEqual(values['settings/charge-mode'], '4719')
