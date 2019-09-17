"""
Utility functions for Labber features
"""

### Expiration conditions

def no_recorded_result(feature, level=0):
    """
    Expiration condition: is there a result?
    """
    return not len(feature.log_history) > 0

