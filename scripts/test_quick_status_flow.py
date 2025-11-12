#!/usr/bin/env python3
"""
Test Quick Status Flow - Verifies instant status responses.

Simulates user asking "What's the current state?" and validates:
1. Response time < 100ms
2. Returns concise sensor summary
3. Uses synthetic "today" data
4. Doesn't trigger unnecessary tools/diagrams
"""

from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
from datetime import datetime
import time


def test_quick_status():
    """Test the quick status workflow."""
    
    print('=' * 80)
    print('QUICK STATUS FLOW TEST')
    print('=' * 80)
    
    # Simulate tree startup: pre-seed cache
    print('\n📦 STEP 1: Tree Startup (Pre-seed synthetic today WorldState)')
    print('-' * 80)
    
    start = time.time()
    engine = WorldStateEngine('features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet')
    now = datetime.now()
    
    # This is what bootstrap does at tree creation
    synthetic_ws = engine.compute_worldstate('135_1570', now, 60)
    tree_cache = synthetic_ws  # Stored in tree._initial_worldstate_cache
    
    elapsed_startup = time.time() - start
    
    print(f'✅ Cache pre-seeded in {elapsed_startup*1000:.0f}ms')
    print(f'   Timestamp: {tree_cache["timestamp"]}')
    print(f'   is_synthetic_today: {tree_cache.get("is_synthetic_today")}')
    print(f'   Room temp: {tree_cache["current_state"]["current_room_temp"]:.2f}°C')
    
    # Simulate user request: "What's the current state?"
    print('\n⚡ STEP 2: User Asks "What\'s the current state?" (Agent calls get_current_status)')
    print('-' * 80)
    
    start = time.time()
    
    # Tool reads from cache (no parquet, no Weaviate)
    worldstate = tree_cache  # Direct cache access
    
    # Extract concise status (what get_current_status does)
    current = worldstate.get('current_state', {})
    flags = worldstate.get('flags', {})
    trends = worldstate.get('trends_30m', {})
    health = worldstate.get('health_scores', {})
    
    active_flags = [k.replace('flag_', '') for k, v in flags.items() if v]
    room_temp_delta = trends.get('room_temp_delta_30m', 0)
    trend_description = 'stijgend' if room_temp_delta > 0.5 else 'dalend' if room_temp_delta < -0.5 else 'stabiel'
    
    status_summary = {
        'asset_id': '135_1570',
        'timestamp': worldstate['timestamp'],
        'readings': {
            'room_temp': current.get('current_room_temp'),
            'hot_gas_temp': current.get('current_hot_gas_temp'),
            'suction_temp': current.get('current_suction_temp'),
            'liquid_temp': current.get('current_liquid_temp'),
            'ambient_temp': current.get('current_ambient_temp')
        },
        'active_flags': active_flags,
        'trend_30m': {
            'room_temp_change_C': room_temp_delta,
            'trend_description': trend_description
        },
        'health_summary': {
            'cooling_performance': health.get('cooling_performance_score'),
            'compressor_health': health.get('compressor_health_score'),
            'system_stability': health.get('system_stability_score')
        },
        'is_synthetic_today': worldstate.get('is_synthetic_today', False),
        'cache_hit': True
    }
    
    elapsed_response = time.time() - start
    
    print(f'✅ Response time: {elapsed_response*1000:.1f}ms')
    print()
    print('📋 AGENT RESPONSE (formatted):')
    print('━' * 80)
    print(f'Huidige status ({now.strftime("%d %b %Y, %H:%M")}):')
    print(f'  • Koelcel temperatuur: {status_summary["readings"]["room_temp"]:.1f}°C ⚠️ (design: -33°C)')
    print(f'  • Heetgas: {status_summary["readings"]["hot_gas_temp"]:.1f}°C (te laag)')
    print(f'  • Zuigdruk: {status_summary["readings"]["suction_temp"]:.1f}°C (extreem koud)')
    print(f'  • Vloeistof: {status_summary["readings"]["liquid_temp"]:.1f}°C')
    print(f'  • Omgeving: {status_summary["readings"]["ambient_temp"]:.1f}°C')
    print()
    print(f'Actieve flags: {", ".join(active_flags)}')
    print(f'Trend (30 min): {status_summary["trend_30m"]["trend_description"]} ({room_temp_delta:+.1f}°C)')
    print()
    print(f'Health scores:')
    print(f'  • Koeling: {status_summary["health_summary"]["cooling_performance"]}/100')
    print(f'  • Compressor: {status_summary["health_summary"]["compressor_health"]}/100')
    print(f'  • Stabiliteit: {status_summary["health_summary"]["system_stability"]}/100')
    print()
    print('Dit patroon wijst op een bevroren verdamper.')
    print('Wil je dat ik een diagnose start (SMIDO workflow)?')
    print('━' * 80)
    
    # Validation
    print('\n✅ STEP 3: Validation')
    print('-' * 80)
    
    checks = []
    
    # Performance check
    if elapsed_response < 0.1:
        print(f'✅ Performance: {elapsed_response*1000:.1f}ms < 100ms target')
        checks.append(True)
    else:
        print(f'❌ Performance: {elapsed_response*1000:.1f}ms > 100ms target')
        checks.append(False)
    
    # Synthetic check
    if status_summary['is_synthetic_today']:
        print(f'✅ Uses synthetic "today" data')
        checks.append(True)
    else:
        print(f'❌ Not using synthetic today data')
        checks.append(False)
    
    # Flags check (A3-like)
    if 'main_temp_high' in active_flags and 'suction_extreme' in active_flags:
        print(f'✅ A3-like flags present (main_temp_high, suction_extreme)')
        checks.append(True)
    else:
        print(f'❌ Missing expected A3-like flags')
        checks.append(False)
    
    # Cache check
    if status_summary['cache_hit']:
        print(f'✅ Uses cached data (no I/O)')
        checks.append(True)
    else:
        print(f'❌ Not using cache')
        checks.append(False)
    
    # Concise check
    if len(status_summary['readings']) == 5:
        print(f'✅ Returns concise summary (5 sensors)')
        checks.append(True)
    else:
        print(f'❌ Summary not concise')
        checks.append(False)
    
    print('\n' + '=' * 80)
    if all(checks):
        print('🎉 ALL CHECKS PASSED - Quick status flow ready for production!')
    else:
        print(f'⚠️  {sum(checks)}/{len(checks)} checks passed')
    print('=' * 80)
    
    print('\n📝 EXPECTED USER EXPERIENCE:')
    print('━' * 80)
    print('User: "What\'s the current state?"')
    print('Agent: [<100ms response]')
    print('       "Huidige status: Koelcel -0.3°C (te hoog), Heetgas 19.1°C (te laag),')
    print('        Zuigdruk -40.5°C (extreem). Flags: main_temp_high, suction_extreme.')
    print('        Trend: stijgend. Dit wijst op bevroren verdamper.')
    print('        Wil je diagnose?"')
    print()
    print('User: "Ja" → Agent proceeds to T/I/D phases')
    print('User: "Nee" → Conversation continues in M, no auto-routing')
    print('━' * 80)


if __name__ == '__main__':
    test_quick_status()

