"""
Utility functions and constants for Labber
"""

### Expiration conditions

def no_recorded_result(feature, level=0):
    """
    Expiration condition: is there a result?
    """
    return not len(feature.log_history) > 0

def new_channel():
    """Instantiates a dict containing a template for an empty single-point
    channel.
    """
    return {
        "channel_name": "myChannel",
        "after_last": "Goto first point",
        "alternate_direction": False,
        "equation": "x",
        "final_value": 0.0,
        "optimizer_config": {
            "Enabled": False,
            "Initial step size": 1.0,
            "Max value": 1.0,
            "Min value": 0.0,
            "Precision": 0.001,
            "Start value": 0.5
        },
        "relation_parameters": [
            {
                "channel_name": "Step values",
                "lookup": None,
                "use_lookup": False,
                "variable": "x"
            }
        ],
        "show_advanced": False,
        "step_items": [
            {
                "center": 0.0,
                "interp": "Linear",
                "n_pts": 1,
                "range_type": "Single",
                "single": 1.0,
                "span": 0.0,
                "start": 1.0,
                "step": 0.0,
                "step_type": "Fixed # of pts",
                "stop": 1.0,
                "sweep_rate": 0.0
            }
        ],
        "step_unit": "Instrument",
        "sweep_mode": "Off",
        "sweep_rate_outside": 0.0,
        "use_outside_sweep_rate": False,
        "use_relations": False,
        "wait_after": 0.0
    }

