import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/heart_inputs.dart';

/// Result from the trained forest. Probability is the model's class-1 output.
class PredictionResult {
  const PredictionResult({required this.hasHeartDisease, this.probability});

  final bool hasHeartDisease;
  final double? probability;
}

/// Offline evaluator for the supplied RandomForestClassifier.
///
/// The JSON asset contains only the fitted sklearn tree parameters. This class
/// follows the recorded feature order and aggregates each leaf's class
/// probabilities as sklearn's RandomForestClassifier.predict_proba does.
class PredictionService {
  const PredictionService();

  static const _assetPath = 'assets/models/heart_disease_rf_model.json';
  static const _expectedFeatures = [
    'age',
    'sex',
    'blood_pressure',
    'cholesterol',
    'bmi',
    'smoker',
    'diabetes',
    'physical_activity',
    'family_history',
    'stress_level',
  ];

  static Future<_Forest>? _forestFuture;

  bool get isConfigured => true;

  Future<PredictionResult> predict(HeartInputs inputs) async {
    final forest = await (_forestFuture ??= _loadForest());
    final features = <double>[
      inputs.age.toDouble(),
      inputs.sex.toDouble(),
      inputs.bloodPressure,
      inputs.cholesterol,
      inputs.bmi,
      inputs.smoker.toDouble(),
      inputs.diabetes.toDouble(),
      inputs.physicalActivity.toDouble(),
      inputs.familyHistory.toDouble(),
      inputs.stressLevel.toDouble(),
    ];
    if (features.length != forest.featureNames.length ||
        features.any((value) => !value.isFinite)) {
      throw StateError('Input values do not match the model feature contract.');
    }

    final classTotals = List<double>.filled(forest.classes.length, 0);
    for (final tree in forest.trees) {
      final leaf = tree.leafFor(features);
      final probabilities = tree.leafProbabilities[leaf];
      if (probabilities == null || probabilities.length != classTotals.length) {
        throw StateError('The model contains an invalid leaf output.');
      }
      for (var i = 0; i < classTotals.length; i++) {
        classTotals[i] += probabilities[i];
      }
    }

    for (var i = 0; i < classTotals.length; i++) {
      classTotals[i] /= forest.trees.length;
    }
    var predictedIndex = 0;
    for (var i = 1; i < classTotals.length; i++) {
      if (classTotals[i] > classTotals[predictedIndex]) predictedIndex = i;
    }
    final positiveIndex = forest.classes.indexOf(1);
    if (positiveIndex < 0) {
      throw StateError(
        'The model does not contain the configured disease class.',
      );
    }
    return PredictionResult(
      hasHeartDisease: forest.classes[predictedIndex] == 1,
      probability: classTotals[positiveIndex],
    );
  }

  static Future<_Forest> _loadForest() async {
    final source = await rootBundle.loadString(_assetPath);
    final decoded = jsonDecode(source);
    if (decoded is! Map<String, dynamic> ||
        decoded['format'] != 'heart-risk-random-forest-v1') {
      throw StateError('The bundled model asset has an unsupported format.');
    }
    final features = (decoded['featureNames'] as List<dynamic>).cast<String>();
    if (features.length != _expectedFeatures.length) {
      throw StateError('The model has an unexpected number of input features.');
    }
    for (var i = 0; i < features.length; i++) {
      if (features[i] != _expectedFeatures[i]) {
        throw StateError(
          'The bundled model feature order does not match the app.',
        );
      }
    }
    final classes = (decoded['classes'] as List<dynamic>)
        .map((value) => (value as num).toInt())
        .toList(growable: false);
    if (classes.length != 2 || !classes.contains(0) || !classes.contains(1)) {
      throw StateError('The model must contain binary classes 0 and 1.');
    }
    final trees = (decoded['trees'] as List<dynamic>)
        .map((value) => _Tree.fromJson(value as Map<String, dynamic>))
        .toList(growable: false);
    if (trees.isEmpty) throw StateError('The model has no fitted trees.');
    return _Forest(featureNames: features, classes: classes, trees: trees);
  }
}

class _Forest {
  const _Forest({
    required this.featureNames,
    required this.classes,
    required this.trees,
  });

  final List<String> featureNames;
  final List<int> classes;
  final List<_Tree> trees;
}

class _Tree {
  const _Tree({
    required this.left,
    required this.right,
    required this.feature,
    required this.threshold,
    required this.leafProbabilities,
  });

  final List<int> left;
  final List<int> right;
  final List<int> feature;
  final List<double> threshold;
  final List<List<double>?> leafProbabilities;

  factory _Tree.fromJson(Map<String, dynamic> json) {
    final left = (json['left'] as List<dynamic>)
        .map((value) => (value as num).toInt())
        .toList(growable: false);
    final right = (json['right'] as List<dynamic>)
        .map((value) => (value as num).toInt())
        .toList(growable: false);
    final feature = (json['feature'] as List<dynamic>)
        .map((value) => (value as num).toInt())
        .toList(growable: false);
    final threshold = (json['threshold'] as List<dynamic>)
        .map((value) => (value as num).toDouble())
        .toList(growable: false);
    final leaves = (json['leafProbabilities'] as List<dynamic>)
        .map(
          (value) => value == null
              ? null
              : (value as List<dynamic>)
                    .map((item) => (item as num).toDouble())
                    .toList(growable: false),
        )
        .toList(growable: false);
    final count = left.length;
    if (count == 0 ||
        right.length != count ||
        feature.length != count ||
        threshold.length != count ||
        leaves.length != count) {
      throw StateError('The bundled model contains an invalid tree.');
    }
    return _Tree(
      left: left,
      right: right,
      feature: feature,
      threshold: threshold,
      leafProbabilities: leaves,
    );
  }

  int leafFor(List<double> values) {
    var node = 0;
    var steps = 0;
    while (leafProbabilities[node] == null) {
      if (++steps > left.length) {
        throw StateError('The bundled model contains a cyclic tree.');
      }
      final featureIndex = feature[node];
      if (featureIndex < 0 || featureIndex >= values.length) {
        throw StateError(
          'The bundled model contains an invalid feature index.',
        );
      }
      node = values[featureIndex] <= threshold[node] ? left[node] : right[node];
      if (node < 0 || node >= left.length) {
        throw StateError('The bundled model contains an invalid tree branch.');
      }
    }
    return node;
  }
}
