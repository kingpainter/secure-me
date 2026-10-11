"""Unit tests for SensorGroup debouncing and anti-masking."""

import time
import pytest
from unittest.mock import patch
from custom_components.secure_me.zones import SensorGroup


class TestSensorGroupDebouncing:
    """Test SensorGroup.record_activation() boundary conditions."""

    def test_no_timeout_activates_immediately_at_threshold(self):
        """With timeout=0, activations count regardless of timing."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=0,
            event_count=2,
        )
        
        # First activation: 0/2
        result1 = group.record_activation("sensor.a")
        assert result1 is False
        
        # Second activation: 2/2 -> threshold met immediately
        result2 = group.record_activation("sensor.b")
        assert result2 is True

    def test_same_sensor_multiple_times_counts_once(self):
        """Same sensor recorded multiple times only counts once."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=10,
            event_count=2,
        )
        
        # Record same sensor multiple times
        group.record_activation("sensor.a")
        group.record_activation("sensor.a")
        group.record_activation("sensor.a")
        
        # Still only 1 unique sensor -> threshold not met
        assert len(group._activations) == 1
        result = group.record_activation("sensor.a")
        assert result is False

    @patch("time.monotonic")
    def test_activation_at_exact_timeout_boundary_included(self, mock_time):
        """Activation exactly at timeout boundary (>= cutoff) should be included."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=10,
            event_count=1,
        )
        
        # Record first sensor at time 0
        mock_time.return_value = 0.0
        group.record_activation("sensor.a")
        
        # Jump to exactly 10 seconds later (at the boundary)
        # cutoff = 10 - 10 = 0, so activation at ts=0 should satisfy ts >= 0
        mock_time.return_value = 10.0
        result = group.record_activation("sensor.b")
        
        # Both activations should be retained (the first one at ts=0 >= cutoff=0)
        assert len(group._activations) == 2
        assert result is True

    @patch("time.monotonic")
    def test_activation_just_before_timeout_boundary_excluded(self, mock_time):
        """Activation just before timeout boundary should be excluded."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=10,
            event_count=2,
        )
        
        # Record first sensor at time 0
        mock_time.return_value = 0.0
        group.record_activation("sensor.a")
        
        # Jump to 10.01 seconds later (just beyond the timeout window)
        # cutoff = 10.01 - 10 = 0.01, so activation at ts=0 < 0.01 excluded
        mock_time.return_value = 10.01
        result = group.record_activation("sensor.b")
        
        # First activation should be purged, only second remains
        assert len(group._activations) == 1
        assert result is False

    @patch("time.monotonic")
    def test_multiple_sensors_within_timeout_window(self, mock_time):
        """Multiple sensors activating within timeout window."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b", "sensor.c"],
            timeout=5,
            event_count=3,
        )
        
        # t=0: sensor.a
        mock_time.return_value = 0.0
        group.record_activation("sensor.a")
        assert len(group._activations) == 1
        
        # t=2: sensor.b (within 5s window of first)
        mock_time.return_value = 2.0
        group.record_activation("sensor.b")
        assert len(group._activations) == 2
        
        # t=4.5: sensor.c (within 5s window of first at t=0)
        # cutoff = 4.5 - 5 = -0.5, so all ts >= -0.5 remain
        mock_time.return_value = 4.5
        result = group.record_activation("sensor.c")
        assert len(group._activations) == 3
        assert result is True

    @patch("time.monotonic")
    def test_sliding_window_cleans_old_activations(self, mock_time):
        """Timeout window slides forward, removing stale activations."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b", "sensor.c"],
            timeout=5,
            event_count=2,
        )
        
        # t=0: sensor.a
        mock_time.return_value = 0.0
        group.record_activation("sensor.a")
        assert len(group._activations) == 1
        
        # t=4: sensor.b (within window)
        mock_time.return_value = 4.0
        result = group.record_activation("sensor.b")
        assert len(group._activations) == 2
        assert result is True
        
        # t=5.5: sensor.c
        # cutoff = 5.5 - 5 = 0.5
        # sensor.a at t=0 < 0.5 gets purged
        # sensor.b at t=4 >= 0.5 remains
        mock_time.return_value = 5.5
        result = group.record_activation("sensor.c")
        assert len(group._activations) == 2
        assert result is True
        assert "sensor.a" not in group._activations
        assert "sensor.b" in group._activations
        assert "sensor.c" in group._activations

    def test_reset_clears_all_activations(self):
        """reset() should clear all activation records."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=10,
            event_count=2,
        )
        
        group.record_activation("sensor.a")
        group.record_activation("sensor.b")
        assert len(group._activations) == 2
        
        group.reset()
        assert len(group._activations) == 0

    def test_event_count_threshold_enforcement(self):
        """Threshold only met when active_count >= event_count."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b", "sensor.c"],
            timeout=0,
            event_count=3,
        )
        
        # 1/3
        assert group.record_activation("sensor.a") is False
        
        # 2/3
        assert group.record_activation("sensor.b") is False
        
        # 3/3 -> threshold met
        assert group.record_activation("sensor.c") is True

    def test_zero_event_count_edge_case(self):
        """event_count=0 is an edge case (any activation triggers)."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a"],
            timeout=0,
            event_count=0,
        )
        
        # 0 >= 0, so immediately true even before any activation
        # Actually: on first activation, _activations becomes {sensor.a: ts}
        # len = 1, 1 >= 0 is True
        result = group.record_activation("sensor.a")
        assert result is True

    @patch("time.monotonic")
    def test_timeout_zero_disables_window(self, mock_time):
        """timeout=0 means all activations count regardless of timing."""
        group = SensorGroup(
            group_id="g1",
            name="test_group",
            entities=["sensor.a", "sensor.b"],
            timeout=0,
            event_count=2,
        )
        
        # t=0: sensor.a
        mock_time.return_value = 0.0
        group.record_activation("sensor.a")
        
        # t=1000: sensor.b (far in future)
        # With timeout=0, no cleanup happens, so sensor.a is retained
        mock_time.return_value = 1000.0
        result = group.record_activation("sensor.b")
        
        assert len(group._activations) == 2
        assert result is True

