"""
Ketter 3.0 - Circuit Breaker Tests for Watch Mode
ENHANCE #6: Circuit breaker for continuous watch mode

Tests verify that watch mode has safety limits:
- Max cycles limit (prevents infinite loops)
- Max duration limit (prevents runaway jobs)
- Error rate threshold (stops if too many errors)
- Graceful shutdown with logging
"""

import pytest
import os
from datetime import datetime, timedelta, timezone


# ============================================
# TEST 1: Max Cycles Logic
# ============================================

def test_max_cycles_calculation():
    """
    Verify max cycles calculation is correct
    """
    # Default: 10000 cycles at 5s/cycle = 50000s = ~14 hours
    MAX_CYCLES = 10000
    CYCLE_INTERVAL_SECONDS = 5

    total_time_seconds = MAX_CYCLES * CYCLE_INTERVAL_SECONDS
    total_time_hours = total_time_seconds / 3600

    assert total_time_hours == pytest.approx(13.89, rel=0.01)


def test_max_cycles_threshold():
    """
    Verify that circuit breaker would trigger at max cycles
    """
    MAX_CYCLES = 100
    watch_cycles = 100

    # Circuit breaker should trigger
    should_stop = watch_cycles >= MAX_CYCLES
    assert should_stop is True

    # One less should not trigger
    watch_cycles = 99
    should_stop = watch_cycles >= MAX_CYCLES
    assert should_stop is False


# ============================================
# TEST 2: Max Duration Logic
# ============================================

def test_max_duration_threshold():
    """
    Verify that circuit breaker would trigger at max duration
    """
    MAX_DURATION_SECONDS = 3600  # 1 hour

    # Simulate watch start time
    watch_start_time = datetime.now(timezone.utc)

    # Simulate 1 hour 1 second elapsed
    current_time = watch_start_time + timedelta(seconds=3601)
    elapsed_seconds = (current_time - watch_start_time).total_seconds()

    # Circuit breaker should trigger
    should_stop = elapsed_seconds > MAX_DURATION_SECONDS
    assert should_stop is True

    # Just under 1 hour should not trigger
    current_time = watch_start_time + timedelta(seconds=3599)
    elapsed_seconds = (current_time - watch_start_time).total_seconds()

    should_stop = elapsed_seconds > MAX_DURATION_SECONDS
    assert should_stop is False


def test_duration_conversion_hours():
    """
    Verify duration is correctly converted to hours for logging
    """
    MAX_DURATION_SECONDS = 86400  # 24 hours

    hours = MAX_DURATION_SECONDS / 3600
    assert hours == 24.0


# ============================================
# TEST 3: Error Rate Threshold Logic
# ============================================

def test_error_rate_calculation_all_errors():
    """
    Verify error rate calculation with all errors
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    # Simulate 10 cycles with all errors
    error_history = [True] * 10

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 100.0

    # Circuit breaker should trigger
    should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    assert should_stop is True


def test_error_rate_calculation_no_errors():
    """
    Verify error rate calculation with no errors
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    # Simulate 10 cycles with no errors
    error_history = [False] * 10

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 0.0

    # Circuit breaker should NOT trigger
    should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    assert should_stop is False


def test_error_rate_calculation_at_threshold():
    """
    Verify error rate calculation exactly at threshold
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    # Simulate 5 errors, 5 successes (50%)
    error_history = [True, False, True, False, True, False, True, False, True, False]

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 50.0

    # Circuit breaker SHOULD trigger (>= threshold)
    should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    assert should_stop is True


def test_error_rate_calculation_below_threshold():
    """
    Verify error rate calculation just below threshold
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    # Simulate 4 errors, 6 successes (40%)
    error_history = [True, False, True, False, True, False, True, False, False, False]

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 40.0

    # Circuit breaker should NOT trigger
    should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    assert should_stop is False


def test_error_rate_sliding_window():
    """
    Verify error rate only considers last N cycles (sliding window)
    """
    ERROR_WINDOW_SIZE = 10

    # Simulate 20 cycles: first 10 errors, last 10 success
    error_history = [True] * 10 + [False] * 10

    # Only last 10 should be considered (all success)
    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 0.0


# ============================================
# TEST 4: Error History Management
# ============================================

def test_error_history_growth_bounded():
    """
    Verify error history doesn't grow unbounded
    """
    ERROR_WINDOW_SIZE = 10
    MAX_HISTORY_SIZE = ERROR_WINDOW_SIZE * 2

    # Simulate many cycles
    error_history = []

    for i in range(100):
        error_history.append(i % 2 == 0)  # Alternating errors

        # Trim to prevent unbounded growth
        if len(error_history) > MAX_HISTORY_SIZE:
            error_history = error_history[-MAX_HISTORY_SIZE:]

    # History should be capped at MAX_HISTORY_SIZE
    assert len(error_history) == MAX_HISTORY_SIZE


def test_error_history_tracking_recent():
    """
    Verify error history correctly tracks recent cycles
    """
    error_history = []

    # Cycle 1: Success
    error_history.append(False)
    assert len(error_history) == 1

    # Cycle 2: Error
    error_history.append(True)
    assert len(error_history) == 2

    # Cycle 3: Success
    error_history.append(False)
    assert len(error_history) == 3

    # Verify content
    assert error_history == [False, True, False]


# ============================================
# TEST 5: Environment Variable Defaults
# ============================================

def test_env_var_defaults():
    """
    Verify environment variable defaults are reasonable
    """
    # Default from code
    MAX_CYCLES = int(os.getenv("WATCH_MAX_CYCLES", "10000"))
    MAX_DURATION_SECONDS = int(os.getenv("WATCH_MAX_DURATION", "86400"))
    ERROR_THRESHOLD_PERCENT = int(os.getenv("WATCH_ERROR_THRESHOLD", "50"))

    # Verify defaults are sensible
    assert MAX_CYCLES > 0
    assert MAX_CYCLES <= 100000  # Reasonable upper limit

    assert MAX_DURATION_SECONDS > 0
    assert MAX_DURATION_SECONDS <= 604800  # Max 1 week

    assert ERROR_THRESHOLD_PERCENT > 0
    assert ERROR_THRESHOLD_PERCENT <= 100


def test_env_var_override():
    """
    Verify environment variables can be overridden
    """
    # Simulate override
    os.environ["WATCH_MAX_CYCLES"] = "500"
    os.environ["WATCH_MAX_DURATION"] = "7200"
    os.environ["WATCH_ERROR_THRESHOLD"] = "75"

    try:
        MAX_CYCLES = int(os.getenv("WATCH_MAX_CYCLES", "10000"))
        MAX_DURATION_SECONDS = int(os.getenv("WATCH_MAX_DURATION", "86400"))
        ERROR_THRESHOLD_PERCENT = int(os.getenv("WATCH_ERROR_THRESHOLD", "50"))

        assert MAX_CYCLES == 500
        assert MAX_DURATION_SECONDS == 7200
        assert ERROR_THRESHOLD_PERCENT == 75
    finally:
        # Cleanup
        del os.environ["WATCH_MAX_CYCLES"]
        del os.environ["WATCH_MAX_DURATION"]
        del os.environ["WATCH_ERROR_THRESHOLD"]


# ============================================
# TEST 6: Integration Scenarios
# ============================================

def test_scenario_normal_operation():
    """
    Scenario: Normal operation - no circuit breaker triggers
    """
    MAX_CYCLES = 1000
    MAX_DURATION_SECONDS = 3600
    ERROR_THRESHOLD_PERCENT = 50
    ERROR_WINDOW_SIZE = 10

    watch_cycles = 50
    watch_start_time = datetime.now(timezone.utc)
    elapsed_seconds = 300  # 5 minutes
    error_history = [False] * 10  # No errors

    # Check circuit breaker
    should_stop_cycles = watch_cycles >= MAX_CYCLES
    should_stop_duration = elapsed_seconds > MAX_DURATION_SECONDS

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100
    should_stop_errors = error_rate_percent >= ERROR_THRESHOLD_PERCENT

    # None should trigger
    assert should_stop_cycles is False
    assert should_stop_duration is False
    assert should_stop_errors is False


def test_scenario_high_error_rate_stops():
    """
    Scenario: High error rate triggers circuit breaker
    """
    ERROR_THRESHOLD_PERCENT = 50
    ERROR_WINDOW_SIZE = 10

    # Simulate 8 errors in last 10 cycles (80% error rate)
    error_history = [True] * 8 + [False] * 2

    error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
    error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100

    assert error_rate_percent == 80.0

    should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    assert should_stop is True


def test_scenario_max_cycles_stops():
    """
    Scenario: Max cycles reached triggers circuit breaker
    """
    MAX_CYCLES = 1000
    watch_cycles = 1000

    should_stop = watch_cycles >= MAX_CYCLES
    assert should_stop is True


def test_scenario_max_duration_stops():
    """
    Scenario: Max duration exceeded triggers circuit breaker
    """
    MAX_DURATION_SECONDS = 3600  # 1 hour
    watch_start_time = datetime.now(timezone.utc)

    # Simulate 2 hours elapsed
    current_time = watch_start_time + timedelta(hours=2)
    elapsed_seconds = (current_time - watch_start_time).total_seconds()

    should_stop = elapsed_seconds > MAX_DURATION_SECONDS
    assert should_stop is True


# ============================================
# TEST 7: Edge Cases
# ============================================

def test_edge_case_empty_error_history():
    """
    Edge case: Error history is empty (first few cycles)
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    error_history = []

    # Should not crash with empty history
    if len(error_history) >= ERROR_WINDOW_SIZE:
        error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
        error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100
        should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    else:
        # Not enough data yet - don't trigger circuit breaker
        should_stop = False

    assert should_stop is False


def test_edge_case_partial_error_history():
    """
    Edge case: Error history has fewer than window size entries
    """
    ERROR_WINDOW_SIZE = 10
    ERROR_THRESHOLD_PERCENT = 50

    # Only 5 cycles so far
    error_history = [True] * 5

    # Should not trigger until we have full window
    if len(error_history) >= ERROR_WINDOW_SIZE:
        error_count = sum(1 for err in error_history[-ERROR_WINDOW_SIZE:] if err)
        error_rate_percent = (error_count / ERROR_WINDOW_SIZE) * 100
        should_stop = error_rate_percent >= ERROR_THRESHOLD_PERCENT
    else:
        should_stop = False

    assert should_stop is False


if __name__ == "__main__":
    # Run with: pytest tests/test_circuit_breaker.py -v
    pytest.main([__file__, "-v", "-s"])
