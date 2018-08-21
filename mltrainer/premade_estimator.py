from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import tensorflow as tf

import sensor_data


parser = argparse.ArgumentParser()
parser.add_argument('--batch_size', default=1000, type=int, help='batch size')
parser.add_argument('--train_steps', default=15000, type=int, help='number of training steps')

def main(argv):
    args = parser.parse_args(argv[1:])
    (train_x, train_y), (test_x, test_y) = sensor_data.load_data()

    my_feature_columns = []
    for key in train_x.keys():
        my_feature_columns.append(tf.feature_column.numeric_column(key=key))
    classifier = tf.estimator.DNNClassifier(
        feature_columns=my_feature_columns,
        hidden_units=[64, 64, 64, 64],
        n_classes=6)

    classifier.train(
        input_fn=lambda:sensor_data.train_input_fn(train_x, train_y, args.batch_size),
        steps=args.train_steps)

    eval_result = classifier.evaluate(
        input_fn=lambda:sensor_data.eval_input_fn(test_x, test_y, args.batch_size))

    print('\nTest set accuracy: {accuracy:0.3f}\n'.format(**eval_result))

    feature_spec = tf.feature_column.make_parse_example_spec(my_feature_columns)
    export_input_fn = tf.estimator.export.build_parsing_serving_input_receiver_fn(feature_spec)
    classifier.export_savedmodel('/home/gustavo_rozatti/model/', sensor_data.serving_input_receiver_fn)

    expected = ['4', '2', '3', '1', '4']
    predict_x = {
        'temperature': [44.9, 39.3, 33.9, 30.6, 49.6],
        'pressure': [1012.0, 1012.0, 1011.0, 1011.0, 1013.0],
        'humidity': [63.0, 81.0, 69.0, 88.0, 62.0],
        'dewpoint': [31.5, 32.3, 22.8, 26.3, 35.9]
    }

    predictions = classifier.predict( input_fn=lambda:sensor_data.eval_input_fn(predict_x, labels=None, batch_size=args.batch_size))

    template = ('\nPrediction is "{}" ({:.1f}%), expected "{}"')

    for pred_dict, expec in zip(predictions, expected):
        class_id = pred_dict['class_ids'][0]
        probability = pred_dict['probabilities'][class_id]

        print(template.format(sensor_data.SCORES[class_id], 100 * probability, expec))


if __name__ == '__main__':
    tf.logging.set_verbosity(tf.logging.WARN)
    tf.app.run(main)

