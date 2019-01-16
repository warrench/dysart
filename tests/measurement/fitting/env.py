import sys
import os

# append module root directory to sys.path
sys.path.append(
    os.path.dirname(
        os.path.relpath('../../../..')
    )
)

# some constants, such as the location of sample data
data_file_path = '../../sample_data/'
