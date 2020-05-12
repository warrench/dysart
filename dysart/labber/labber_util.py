"""
Utility functions and constants for Labber
"""

from typing import *

import dysart.messages.errors as errors


def no_recorded_result(feature, level=0):
    """
    Expiration condition: is there a result?
    """
    return not len(feature.log_history) > 0


def new_step_channel():
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


def get_step_channel(config: Dict, diff_key: str) -> Dict:
    """

    Args:
        config: 
        diff_key: 

    Returns:

    """
    return next(c for c in config['step_channels'] if
                c['channel_name'] == diff_key)


def get_or_make_step_channel(config: Dict, diff_key: str) -> Dict:
    """Returns an existing step channel from a Labber scenario,
    or makes one if it does not already exist.

    Args:
        config:
        diff_key:

    Returns:

    """
    try:
        channel = get_step_channel(config, diff_key)
    except StopIteration:
        channel = new_step_channel()
    return channel


def get_scalar_channel(config: Dict, diff_key: str) -> Tuple[Dict, str]:
    """
    
    Args:
        config: 
        diff_key: 

    Returns: A pair of an instrument dictionary and the name of the channel.
    
    Raises:
        InstrumentNotFoundError: if there is no instrument named according
        to the first ` - `-separated component of the key.

    """
    # Break e.g. "Holzworth - TWPA pump - Frequency" into
    # "Holzworth", "TWPA pump - Frequency"
    inst_name, chan_name = [s.strip() for s in diff_key.split(' - ', maxsplit=1)]

    # The channel name may be an alias; resolve the name.
    inst_chans = [chan for chan in config['channels']
                  if chan['instrument'] == inst_name]
    chan_name = next((chan['quantity'] for chan in inst_chans
                      if chan.get('name') == chan_name),
                     chan_name)

    # Get the instrument to modify one of its values.
    try:
        inst = next(inst for inst in config['instruments']
                    if inst['com_config']['name'] == inst_name)
    except StopIteration:
        raise errors.InstrumentNotFoundError(inst_name)

    return inst, chan_name


def merge_tuple(new_config: Dict, diff_key: str, diff_val: Tuple) -> None:
    """

    Args:
        new_config:
        diff_key:
        diff_val:

    Returns:

    """
    chan = get_step_channel(new_config, diff_key)
    # Since we're overriding this parameter, clear any relation
    chan['equation'] = 'x'
    items = chan['step_items'][0]

    items['start'] = diff_val[0]
    items['stop'] = diff_val[1]
    items['n_pts'] = diff_val[2]
    items['center'] = (diff_val[0] + diff_val[1]) / 2
    items['span'] = diff_val[1] - diff_val[0]
    items['step'] = items['span'] / items['n_pts']


def merge_scalar(new_config: Dict, diff_key: str, diff_val: Union[int, float]) -> None:
    """

    Args:
        new_config:
        diff_key:
        diff_val:

    Returns:

    """

    # If possible, set a step channel _first_, since this is the order of
    # precedence used by Labber.
    # In the step channel case, the key should be of the form
    # 'Instrument - C
    try:
        chan = get_step_channel(new_config, diff_key)
        # Since we're overriding this parameter, clear any relation
        chan['equation'] = 'x'
        items = chan['step_items'][0]
        items['range_type'] = 'Single'
        items['single'] = diff_val
    # If necessary, update a scalar channel. If _this_ fails, just propagate
    # the error.
    except:
        inst, chan_name = get_scalar_channel(new_config, diff_key)
        inst['values'][chan_name] = diff_val
