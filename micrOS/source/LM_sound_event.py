"""
Module for sound pattern recognition with an I2S microphone.
Pattern recognition is achieved by instance-based learning
(nearest neighbor algorithm) where the user can interactively
train the algorithm by labeling events. The training starts
with an empty dataset, and the user needs to label events while
observing system logs to see if there is a new event. After
recording a few events, the user may decide to turn on the
"auto-learn" feature to improve in-sample accuracy, however,
it may also result in overfitting if certain classes become
overrepresented.

Events may be labeled as None if there are no classes recorded, or
the algorithm is uncertain about which label to assign to the event.
Arbitrary number of classes may be created, or one can use binary
classification where events are labeled as '<class name 1>' or '<class name 2>'.

For the usage, execute "sound_event help" or check the section
"Functions for recording and clearing events from the dataset".

----------------
Example:
----------------
picocom --baud 115200 /dev/ttyACM0  <---- the device must be connected through USB
...
Terminal ready
[info] sound_event: {'class': None}
[info] sound_event: {'class': None}
[info] sound_event: {'class': None}  <---- at this point the user decides to label
                                           this event by: record_last_event '<label>'

[info] sound_event: event of length 8320 will be recorded as "finger_snaps"
                                     <---- resulting log entry after record_last_event

[info] sound_event: {'class': "finger_snaps"}
                                     <---- resulting log entry after recognizing an event
"""

import LM_i2s_mic
import json

from microIO import pinmap_search
from Common import micro_task, syslog, console
from Types import resolve


class Data:
    CONTROL_TASK_TAG = 'sound_event._classifier'
    DATASET = ''
    EVENTS = []
    EVENT_CALLBACKS = set()
    AUTO_LEARN = False
    PERFORMANCE = {}
    DISTANCE_MATRICES = {}


################################################################################
# DSP helper functions
################################################################################


def _amplitude_envelope(samples, frame_size):
    """
    Calculate max amplitude per frame and return it as a list.
    :param frame_size: size of the signal frame (int)
    :param samples: list of sampled values
    """
    envelope = []
    for k in range(int(len(samples)/frame_size)):
        amplitude = [abs(s) for s in samples[k*frame_size: min(len(samples), (k+1)*frame_size)]]
        envelope.append(max(amplitude))

    return envelope


def _rmse(samples, frame_size):
    """
    Calculate root mean squared energy.
    :param frame_size: size of the signal frame (int)
    :param samples: list of sampled values
    """
    rmse = []
    for k in range(int(len(samples)/frame_size)):
        rmse_frame = (sum([s**2 for s in samples[k*frame_size: min(len(samples), (k+1)*frame_size)]])/frame_size)**(0.5)
        rmse.append(rmse_frame)

    return rmse


def _zero_crossing_rate(samples, frame_size):
    """
    Calculate the rate of the signal crossing the X axis.
    :param frame_size: size of the signal frame (int)
    :param samples: list of sampled values
    """
    rates = []
    for k in range(int(len(samples)/frame_size)):
        rate = 0
        for i in range(k*frame_size, min(len(samples)-1, (k+1)*frame_size-1)):
            rate += abs(samples[i]/abs(samples[i]) - samples[i+1]/abs(samples[i+1]))
        rates.append(0.5 * rate)

    return rates


def _crest_factor(samples, frame_size):
    """
    Calculate Crest factor (peak amplitude divided by RMSE).
    :param frame_size: size of the signal frame (int)
    :param samples: list of sampled values
    """
    cf = []
    for k in range(int(len(samples)/frame_size)):
        peak = max(samples[k*frame_size: min(len(samples), (k+1)*frame_size)], key=lambda x: abs(x))
        rmse_frame = (sum([s**2 for s in samples[k*frame_size: min(len(samples), (k+1)*frame_size)]])/frame_size)**(0.5)
        cf.append(peak/rmse_frame)

    return cf


def _analyze_event(samples, frame_size):
    return {
        'name': None,
        'features': {
            'ZCR': {'type': 'time-series', 'data': _zero_crossing_rate(samples,frame_size)},
            'RMSE': {'type': 'time-series', 'data': _rmse(samples,frame_size)},
            'envelope': {'type': 'time-series', 'data': _amplitude_envelope(samples, frame_size)},
            'Crest factor': {'type': 'time-series', 'data': _crest_factor(samples, frame_size)},
            'length': {'type': 'ratio', 'data': len(samples)},
            'max': {'type': 'ratio', 'data': max([abs(s) for s in samples])}
        }
    }

def _get_feature_values(event, feature):
    return event['features'][feature]['data']

def _get_feature_names():
    return ['ZCR', 'RMSE', 'envelope', 'Crest factor', 'length', 'max']


######################################################################################
# Functions for classification (instance-based learning)
# Distance between time-dependent features is measured in two steps:
#   1. match the alignment of the signals by maximizing cross-correlation
#   2. measure mean squared error on the aligned signals
#
# Distance between instances is determined by measuring the closest instance by all
# features separately, and selecting the most frequent class by majority voting.
######################################################################################


def _calculate_time_series_feature_distances(instances, i, j, distance_matrices):
    """
    calculate distance matrices time-series data
    :param instances: dict - instances read from dataset
    :param i: int - index of the instance to compare
    :param j: int - index of the other instance to compare
    :param distance_matrices: dict - initialized distance matrices
    """
    time_series_features = [f for f in instances[0]['features'].keys() if instances[0]['features'][f]['type'] == 'time-series']

    if not time_series_features:
        return

    features_i = {}
    features_j = {}
    cross_corr = {}
    l_f = None
    l_g = None

    for feature in time_series_features:
        features_i[feature] = _get_feature_values(instances[i], feature)
        features_j[feature] = _get_feature_values(instances[j], feature)
        cross_corr[feature] = [0]

        if l_f is None:
            l_f = len(features_i[feature])
            l_g = len(features_j[feature])
        elif l_f != len(features_i[feature]) or l_g != len(features_j[feature]):
            raise ValueError('Only time-series features of the same length can be computed at once!')


    cross_corr_range_n = range(-(l_g - 1), l_f)

    for n in cross_corr_range_n:
        cross_corr_range_m = range(max(0, -n), min(l_f, l_g - n))

        if len(cross_corr_range_m):
            for feature in time_series_features:
                cross_corr[feature].append(0)

        for m in cross_corr_range_m:
            for feature in time_series_features:
                cross_corr[feature][-1] += features_i[feature][m] * features_j[feature][m+n]

    # Best alignment of signals is averaged for all time-dependent features,
    # thereby penalizing misalignment between features.
    n = 0
    for feature in time_series_features:
        argmax_feature_corr = max(range(len(cross_corr[feature])), key=lambda x: cross_corr[feature][x])
        best_alignment = list(cross_corr_range_n)[argmax_feature_corr]
        n += best_alignment/len(time_series_features)

    n = int(n)
    # MSE (mean-squared error)
    for feature in time_series_features:
        measure = 0
        for m in range(max(0, -n), min(l_f, l_g - n)):
            measure += (features_i[feature][m] - features_j[feature][m + n])**2 / len(range(max(0, -n), min(l_f, l_g - n)))
        distance_matrices[feature][i][j] = measure
        distance_matrices[feature][j][i] = measure # Due to matrix symmetry


def _calculate_ratio_feature_distances(instances, i, j, distance_matrices):
    """
    calculate distance matrices ratio-type values
    :param instances: dict - instances read from dataset
    :param i: int - index of the instance to compare
    :param j: int - index of the other instance to compare
    :param distance_matrices: dict - initialized distance matrices
    """
    ratio_features = [f for f in instances[0]['features'].keys() if instances[0]['features'][f]['type'] == 'ratio']

    if not ratio_features:
        return

    for feature in ratio_features:
        distance = abs(_get_feature_values(instances[i], feature) - _get_feature_values(instances[j], feature))
        distance_matrices[feature][i][j] = distance
        distance_matrices[feature][j][i] = distance # Due to matrix symmetry


def _calculate_all_sound_feature_distances(instances):
    """
    calculate distance matrices from scratch,
    should only be used during initialization
    :param instances: dict - instances read from dataset
    """
    num_instances = len(instances)

    if num_instances:
        distance_matrices = {k: [] for k in set(instances[0]['features'].keys())}
    else:
        distance_matrices = {k: [] for k in _get_feature_names()}

    for i in instances:
        # Initialize empty distance matrices
        for feature in distance_matrices.keys():
            distance_matrices[feature].append([None]*num_instances)


    for i_idx in range(len(instances)):
        for j_idx in range(len(instances)):
            if j_idx > i_idx: # Due to matrix symmetry
                continue
            _calculate_time_series_feature_distances(instances, i_idx, j_idx, distance_matrices)
            _calculate_ratio_feature_distances(instances, i_idx, j_idx, distance_matrices)

    return distance_matrices


def _calculate_sound_feature_distances(instances,
                                      new_instance,
                                      distance_matrices_):
    """
    calculate distance matrices for a new instance
    :param instances: dict - instances read from dataset
    :param new_instance: dict - newly recorded instance to be classified
    :param distances: dict - arbitrary distance matrices
    """
    distance_matrices = {}

    for feature in distance_matrices_.keys():
        distance_matrices[feature] = [r.copy() for r in distance_matrices_[feature]]

        for i in range(len(instances)):
            # Initialize empty columns for the new instance in the distance matrices
            distance_matrices[feature][i].append(0)

    # Add new instance after the existing ones, and create empty row in the distance matrices
    instances.append(new_instance.copy())

    for feature in distance_matrices_.keys():
        distance_matrices[feature].append([0]*(len(instances)))

    for i_idx, i in enumerate(instances):
        _calculate_time_series_feature_distances(instances, i_idx, len(instances)-1, distance_matrices)
        _calculate_ratio_feature_distances(instances, i_idx, len(instances)-1, distance_matrices)
    return distance_matrices


def _classify_instances(instances, distance_matrices):
    """
    classify all instances based on distance matrices
    :param instances: dict - instances read from dataset
    :param distance_matrices: dict - arbitrary distance matrices
    """

    nearest_neighbors = []
    majority_votes = []

    if not len(instances):
        return None

    for i in range(len(instances)):
        votes = []
        majority_vote = None

        for d in distance_matrices.values():
            # Distance of an instance from itself is ignored
            votes.append(min(range(len(d[i])), key=lambda x: d[i][x] if x != i else float('inf')))
        nearest_neighbors.append(votes)

        classes = set(instances[v]['name'] for v in votes)
        class_popularities = {c: sum(c == instances[x]['name'] for x in votes) for c in classes}
        most_popular_class = max(class_popularities.keys(), key=lambda x: class_popularities[x])

        if sum(class_popularities[c] == class_popularities[most_popular_class] for c in class_popularities.keys()) == 1:
            # There is a majority class
            majority_vote = most_popular_class
        else:
            # There is no majority class
            # Calculate most common reciprocal vote
            reciprocal_scores = []
            for v in votes:
                reciprocal_votes = []
                for d in distance_matrices.values():
                    reciprocal_votes.append(min(range(len(d[v])), key=lambda x: d[v][x] if v != x else float('inf')))
                reciprocal_scores.append(sum(instances[r]['name'] == instances[i]['name'] for r in reciprocal_votes))

            if max(reciprocal_scores) and sum(r == max(reciprocal_scores) for r in reciprocal_scores) == 1:
                reciprocal_candidate = max(range(len(reciprocal_scores)), key=lambda x: reciprocal_scores[x])
                majority_vote = instances[votes[reciprocal_candidate]]['name']

        majority_votes.append(majority_vote)

    return nearest_neighbors, majority_votes


def classify_last_event():
    """
    assign a class to the last recorded event
    """
    instances = read_instances()
    if not len(Data.EVENTS):
        return None

    last_event = Data.EVENTS[-1]

    distance_matrices = \
        _calculate_sound_feature_distances(instances, last_event, Data.DISTANCE_MATRICES)
    nearest_neighbors, majority_votes = _classify_instances(instances,distance_matrices)

    if Data.AUTO_LEARN:
        performance_current = Data.PERFORMANCE['in-sample accuracy']
        performance_new = _evaluate_votes(instances,nearest_neighbors,majority_votes)['in-sample accuracy']
        if performance_current < performance_new:
            record_last_event(majority_votes[-1])
            console(f'[info] sound_event: added new instance ({majority_votes[-1]}) to the dataset')
            console(f'[info] sound_event: in-sample accuracy increased from {performance_current} to {performance_new}')

    return {'class': majority_votes[-1]}
        

################################################################################
# I/O helper functions
# Should not be used manually.
################################################################################


def read_instances():
    """
    read stored instances into a dict
    """
    try:
        with open(Data.DATASET, 'r') as f:
            return json.loads(f.read())
    except OSError:
        syslog(f'[ERR] sound_event: unable to read the dataset')
        return []


def _write_instances(instances):
    """
    overwrite instances in the dataset
    :param instances: dict - instances to store
    """
    with open(Data.DATASET, 'w+') as f:
        f.write(json.dumps(instances))


def _init_matrices():
    """
    initialize distance matrices
    """
    instances = read_instances()
    Data.DISTANCE_MATRICES = \
        _calculate_all_sound_feature_distances(instances)

    if len(instances):
        Data.PERFORMANCE = _evaluate_dataset(instances,Data.DISTANCE_MATRICES)
    else:
        console('[info] sound_event: dataset is missing, initializing empty dataset')
        _write_instances([])
        Data.PERFORMANCE = {}


################################################################################
# Functions for recording and clearing events from the dataset
# Can be used during training to save events used for classification.
################################################################################

def record_last_event(label):
    """
    save the last recorded event in the dataset
    :param label: str - name of the class
    """
    console('[info] sound_event: event of length %s will be recorded as "%s"' % (_get_feature_values(Data.EVENTS[-1],'length'), label))
    Data.EVENTS[-1]['name'] = label
    try:
        instances = read_instances()
    except Exception as e:
        syslog(f'[ERR] sound_event: could not read instances (override): {e}')
        instances = []

    instances.append(Data.EVENTS[-1])
    _write_instances(instances)
    _init_matrices()


def remove_last_instance():
    """
    remove the last recorded instance from the dataset
    """
    instances = read_instances()
    instances.pop()
    _write_instances(instances)
    _init_matrices()


def remove_instance_by_idx(idx):
    """
    remove an instance with an index from the dataset
    :param idx: int - index of the instance to be deleted from the dataset
    """
    instances = read_instances()
    del instances[idx]
    _write_instances(instances)
    _init_matrices()


def remove_classes():
    """
    remove all instances from the dataset
    """
    _write_instances([])
    _init_matrices()


def remove_class(class_name):
    """
    remove all instances with the specified label
    :param class_name: str - name of the class
    """
    instances = read_instances()
    new_instances = []

    for instance in instances:
        if instance['name'] != class_name:
            new_instances.append(instance)

    _write_instances(new_instances)
    _init_matrices()


def relabel_class(old_label, new_label):
    """
    rename class used for labeling instances in the dataset
    :param class_name: str - name of the class
    """
    instances = read_instances()

    for instance in instances:
        if instance['name'] == old_label:
            instance['name'] = new_label

    _write_instances(instances)
    _init_matrices()


################################################################################
# Utility functions
################################################################################


def get_classes():
    """
    get all unique classes (labels) stored in the dataset
    """
    instances = read_instances()
    return set([i['name'] for i in instances])


def get_events():
    """
    return all recorded events
    """
    return Data.EVENTS


def _evaluate_votes(instances, nearest_neighbors, majority_votes):
    """
    evaluate classification performance of nearest neighbor results
    with multiple features
    :param instances: dict - instances read from dataset
    :param nearest_neighbors: list - nearest neighbors per feature for each instance
    :param majority_votes: list - names of the classes assigned to the instance
    """
    instances_by_class = {}
    hits_by_class = {}
    accuracy = 0

    for idx, neighbors in enumerate(nearest_neighbors):
        majority_vote = majority_votes[idx]
        ground_truth = instances[idx]['name']

        accuracy += (majority_vote == ground_truth)
        
        if not ground_truth in instances_by_class.keys():
            instances_by_class[ground_truth] = []
        instances_by_class[ground_truth].append(majority_vote == ground_truth)

        if not ground_truth in hits_by_class.keys():
            hits_by_class[ground_truth] = 0
        hits_by_class[ground_truth] += sum([instances[neighbor]['name'] == ground_truth for neighbor in neighbors])/len(neighbors)

    return {
            'in-sample accuracy': accuracy/len(instances), 
            'class accuracies': {c: sum(instances_by_class[c])/len(instances_by_class[c])
                                 for c in instances_by_class.keys()},
            'class consistency': {c: hits_by_class[c]/len(instances_by_class[c])
                                 for c in hits_by_class.keys()}
            }


def _evaluate_dataset(instances,distance_matrices):
    """
    evaluate the in-sample classification performance
    :param instances: dict - instances read from dataset
    :param distance_matrices: dict - arbitrary distance matrices
    """

    nearest_neighbors, majority_votes = _classify_instances(instances, distance_matrices)
    return _evaluate_votes(instances, nearest_neighbors, majority_votes)


def get_performance():
    """
    return the in-sample classification performance
    """
    return Data.PERFORMANCE


################################################################################
# Event loop functions
################################################################################


def autolearn(enabled = True):
    """
    enable/disable automated learning, use it when there are already labeled
    instances in the dataset
    :param enabled: bool
    """
    Data.AUTO_LEARN = enabled


def subscribe(callback, event):
    """
    subscribe to notifications of events
    :callback: func - callback function
    :param event: str - event to get notification for (use 'all' to be notified for all events)
    """
    Data.EVENT_CALLBACKS.add((callback, event))


def _notify(event):
    """
    notification function to invoke callbacks
    :param event: str - class of the currently recorded event
    """
    for callback, observed_event in Data.EVENT_CALLBACKS:
        if event == observed_event or observed_event == 'all':
            callback(event)


def _detect_event(samples, frame_size, pause_frame_count, rmse_threshold = 0.1):
    """
    segment and classify events in samples while maintaining a pointer within
    the raw samples to indicate the last processed sample of an event so that
    the rest can be processed later
    :param samples: list - raw audio samples
    :param frame_size: int - size of an audio frame
    :param pause_frame_count: int - how many pause frame to count for separating events
    :param rmse_threshold: float - RMSE value above which to detect an event (0-1)
    """
    rmse_frames = _rmse(samples, frame_size)
    current_event = []
    events_features = []
    event_pointer = 0
    pause_frames = 0

    # Audio segmentation based on RMSE, and extraction of features
    for i in range(len(rmse_frames)):
        if rmse_frames[i] >= rmse_threshold:
            if not len(current_event):
                event_pointer = i*frame_size
            current_event.extend(samples[i*frame_size : (i+1)*frame_size])
            pause_frames = 0
        else:
            pause_frames += 1
            if len(current_event) and pause_frames <= pause_frame_count:
                current_event.extend(samples[i*frame_size : (i+1)*frame_size])
            else:
                event_pointer = (i+1)*frame_size

                # Finalize and classify event if there are enough pause frames
                if len(current_event) and pause_frames >= pause_frame_count:
                    events_features.append(_analyze_event(current_event, frame_size))
                    current_event = []
                    pause_frames = 0

    return events_features, event_pointer


async def __control_task(capture_duration_ms,
                         max_event_duration_ms,
                         frame_size_ms,
                         pause_duration_ms,
                         event_buffer_length):
    """
    micro task for event detection
    :param capture_duration_ms: int - duration of samples to capture at once
    :param max_event_duration_ms: int - maximum duration of an event
    :param frame_size: int - size of the audio frames used for features
    :param pause_duration_ms: int - duration of pause frames to distinguish events
    :param event_buffer_length: int - number of events to store at once
    """
    with micro_task(tag=Data.CONTROL_TASK_TAG) as my_task:
        samples = []
        frame_size = int((frame_size_ms/1000)*LM_i2s_mic.Data.SAMPLING_RATE)
        pause_duration = int(pause_duration_ms/frame_size_ms)

        while True:
            try:
                new_samples = LM_i2s_mic.decode(await LM_i2s_mic._capture(capture_duration_ms/1000))
                samples.extend(new_samples)

                events, event_pointer = _detect_event(samples, frame_size, pause_duration)
                # Store unprocessed samples to be extended by future samples
                samples = samples[event_pointer:]

                for event in events:
                    Data.EVENTS.append(event)
                    last_event_label = classify_last_event()
                    _notify(last_event_label['class'])
                    console(f'[info] sound_event: {last_event_label}')

                # Discard old samples if the number of stored samples exceeds a threshold
                max_samples = int((max_event_duration_ms/1000)*LM_i2s_mic.Data.SAMPLING_RATE)
                if len(samples) > max_samples:
                    samples = samples[-max_samples:]
                
                # Wait for new samples to be taken
                ms_period = int(len(new_samples)/LM_i2s_mic.Data.SAMPLING_RATE)
                await my_task.feed(sleep_ms=ms_period)
                Data.EVENTS = Data.EVENTS[-event_buffer_length:]
            except Exception as e:
                console(f'[ERR] sound_event: {e}')


def load(dataset = 'sound_events.pds',
         capture_duration_ms=192,
         max_event_duration_ms = 3000,
         frame_size_ms=80,
         pause_duration_ms=500,
         event_buffer_length=1,
         sd_storage=False):
    """
    start micro task for event detection, and mount SD storage if enabled
    :param capture_duration_ms: int - duration of samples to capture at once
    :param max_event_duration_ms: int - maximum duration of an event
    :param frame_size_ms: int - duration of the audio frames used for features
    :param event_buffer_length: int - number of events to store at once
    :param sd_storage: bool - use SD card storage for the dataset
    """
    if sd_storage:
        from vfs import mount
        from machine import SDCard
        mount(SDCard(),"/sd")
        Data.DATASET = f'/sd/{dataset}'
    else:
        Data.DATASET = dataset

    _init_matrices()
    micro_task(tag=Data.CONTROL_TASK_TAG,
               task=__control_task(capture_duration_ms,
                                   max_event_duration_ms,
                                   frame_size_ms,
                                   pause_duration_ms,
                                   event_buffer_length))


#######################
# Helper LM functions #
#######################


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['i2s_sck', 'i2s_ws', 'i2s_sd'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('load dataset=\'sound_events.pds\' capture_duration_ms=192 max_event_duration_ms=3000'\
                    'frame_size_ms=80 pause_duration_ms=500 event_buffer_length=1 sd_storage=False ',\
                    'TEXTBOX classify_last_event',\
                    'read_instances',\
                    'record_last_event label',\
                    'remove_last_instance',\
                    'remove_instance_by_idx idx',\
                    'remove_classes',\
                    'remove_class class_name',\
                    'relabel_class old_label new_label',\
                    'get_classes',\
                    'get_events',\
                    'TEXTBOX get_performance',\
                    'autolearn enabled=True',\
                    'subscribe callback event',\
                    'pinmap'), widgets=widgets)
