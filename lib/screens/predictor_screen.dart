import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/heart_inputs.dart';
import '../services/prediction_service.dart';
import '../widgets/form_field_shell.dart';

class PredictorScreen extends StatefulWidget {
  const PredictorScreen({super.key});

  @override
  State<PredictorScreen> createState() => _PredictorScreenState();
}

class _PredictorScreenState extends State<PredictorScreen> {
  final _formKey = GlobalKey<FormState>();
  final _age = TextEditingController();
  final _bloodPressure = TextEditingController();
  final _cholesterol = TextEditingController();
  final _bmi = TextEditingController();
  final _service = const PredictionService();

  int? _sex;
  int? _smoker;
  int? _diabetes;
  int? _activity;
  int? _familyHistory;
  int? _stress;
  bool _loading = false;
  String? _message;
  PredictionResult? _result;

  static const _disclaimer =
      'This application provides an estimated prediction based on a machine '
      'learning model. It is intended for educational and informational '
      'purposes only and does not constitute a medical diagnosis. The result '
      'should not replace professional medical advice, examination, or '
      'testing. Consult a qualified healthcare professional for medical concerns.';

  @override
  void dispose() {
    _age.dispose();
    _bloodPressure.dispose();
    _cholesterol.dispose();
    _bmi.dispose();
    super.dispose();
  }

  String? _requiredSelection(int? value) =>
      value == null ? 'Please choose an option.' : null;

  String? _positiveNumber(String? value, {required String field}) {
    if (value == null || value.trim().isEmpty) return 'Enter $field.';
    final number = double.tryParse(value.trim());
    if (number == null || !number.isFinite) return 'Enter a valid number.';
    if (number <= 0) return 'Must be greater than 0.';
    return null;
  }

  String? _integerRange(
    String? value, {
    required String field,
    required int min,
    required int max,
  }) {
    if (value == null || value.trim().isEmpty) return 'Enter $field.';
    final number = int.tryParse(value.trim());
    if (number == null) return 'Enter a whole number.';
    if (number < min || number > max) return 'Enter a value from $min to $max.';
    return null;
  }

  Widget _numberField({
    required String label,
    required TextEditingController controller,
    required String hint,
    required String? Function(String?) validator,
    bool decimal = false,
    String? description,
  }) {
    return FormFieldShell(
      label: label,
      description: description,
      child: TextFormField(
        controller: controller,
        keyboardType: TextInputType.numberWithOptions(decimal: decimal),
        inputFormatters: [
          FilteringTextInputFormatter.allow(
            decimal ? RegExp(r'[0-9.]') : RegExp(r'[0-9]'),
          ),
        ],
        decoration: InputDecoration(hintText: hint),
        validator: validator,
        onChanged: (_) => _clearResult(),
      ),
    );
  }

  Widget _selectField({
    required String label,
    required int? value,
    required List<DropdownMenuItem<int>> items,
    required ValueChanged<int?> onChanged,
  }) {
    return FormFieldShell(
      label: label,
      child: DropdownButtonFormField<int>(
        initialValue: value,
        isExpanded: true,
        icon: const Icon(Icons.keyboard_arrow_down_rounded),
        decoration: const InputDecoration(hintText: 'Select an option'),
        items: items,
        validator: _requiredSelection,
        onChanged: (selection) {
          onChanged(selection);
          _clearResult();
        },
      ),
    );
  }

  List<DropdownMenuItem<int>> _yesNoItems() => const [
    DropdownMenuItem(value: 1, child: Text('Yes')),
    DropdownMenuItem(value: 0, child: Text('No')),
  ];

  Widget _fieldGrid(List<Widget> fields, double width) {
    if (width < 660) {
      return Column(
        children: fields
            .map(
              (field) => Padding(
                padding: const EdgeInsets.only(bottom: 18),
                child: field,
              ),
            )
            .toList(),
      );
    }
    return Wrap(
      spacing: 22,
      runSpacing: 18,
      children: fields
          .map((field) => SizedBox(width: (width - 22) / 2, child: field))
          .toList(),
    );
  }

  void _clearResult() {
    if (_result != null || _message != null) {
      setState(() {
        _result = null;
        _message = null;
      });
    }
  }

  Future<void> _check() async {
    FocusScope.of(context).unfocus();
    if (_loading || !(_formKey.currentState?.validate() ?? false)) return;
    if (!_service.isConfigured) {
      setState(() {
        _result = null;
        _message =
            'The trained model is not connected yet. No prediction was '
            'made. Add the supplied model and its verified input contract to '
            'enable this feature.';
      });
      return;
    }

    final inputs = HeartInputs(
      age: int.parse(_age.text),
      sex: _sex!,
      bloodPressure: double.parse(_bloodPressure.text),
      cholesterol: double.parse(_cholesterol.text),
      bmi: double.parse(_bmi.text),
      smoker: _smoker!,
      diabetes: _diabetes!,
      physicalActivity: _activity!,
      familyHistory: _familyHistory!,
      stressLevel: _stress!,
    );

    setState(() {
      _loading = true;
      _message = null;
      _result = null;
    });
    try {
      final result = await _service.predict(inputs);
      if (result.probability != null &&
          (!result.probability!.isFinite ||
              result.probability! < 0 ||
              result.probability! > 1)) {
        throw StateError('Model returned an invalid probability.');
      }
      if (mounted) setState(() => _result = result);
    } catch (_) {
      if (mounted) {
        setState(
          () => _message =
              'The prediction could not be completed. Check the model setup and try again.',
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _reset() {
    _formKey.currentState?.reset();
    _age.clear();
    _bloodPressure.clear();
    _cholesterol.clear();
    _bmi.clear();
    setState(() {
      _sex = null;
      _smoker = null;
      _diabetes = null;
      _activity = null;
      _familyHistory = null;
      _stress = null;
      _message = null;
      _result = null;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final maxWidth = constraints.maxWidth > 900 ? 800.0 : 700.0;
            return Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 22, 20, 36),
                child: ConstrainedBox(
                  constraints: BoxConstraints(maxWidth: maxWidth),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _header(),
                      const SizedBox(height: 22),
                      _formCard(),
                      const SizedBox(height: 18),
                      _resultCard(),
                      const SizedBox(height: 16),
                      _disclaimerCard(),
                      const SizedBox(height: 12),
                      const Center(
                        child: Text(
                          'For educational and informational use',
                          style: TextStyle(
                            color: Color(0xFF728582),
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _header() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: const Color(0xFFE1F2EF),
            borderRadius: BorderRadius.circular(18),
          ),
          child: const Icon(
            Icons.favorite_rounded,
            color: Color(0xFF167D74),
            size: 28,
          ),
        ),
        const SizedBox(width: 14),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Heart Disease Risk Predictor',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              SizedBox(height: 5),
              Text(
                'Enter health details for a model-based estimate.',
                style: TextStyle(fontSize: 13, color: Color(0xFF647874)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _formCard() {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: const BorderSide(color: Color(0xFFE5ECEA)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Your information',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 5),
              const Text(
                'Complete every field. Use the same measurement units used to train your model.',
                style: TextStyle(fontSize: 13, color: Color(0xFF647874)),
              ),
              const SizedBox(height: 22),
              LayoutBuilder(
                builder: (context, constraints) {
                  return _fieldGrid([
                    _numberField(
                      label: 'Age',
                      controller: _age,
                      hint: '1–99 years',
                      validator: (value) => _integerRange(
                        value,
                        field: 'your age',
                        min: 1,
                        max: 99,
                      ),
                    ),
                    _selectField(
                      label: 'Sex',
                      value: _sex,
                      items: const [
                        DropdownMenuItem(value: 1, child: Text('Male')),
                        DropdownMenuItem(value: 0, child: Text('Female')),
                      ],
                      onChanged: (value) => setState(() => _sex = value),
                    ),
                    _numberField(
                      label: 'Blood pressure (mmHg)',
                      controller: _bloodPressure,
                      hint: 'e.g. 120',
                      description: 'Enter the value in mmHg.',
                      decimal: true,
                      validator: (value) =>
                          _positiveNumber(value, field: 'blood pressure'),
                    ),
                    _numberField(
                      label: 'Cholesterol (mg/dL)',
                      controller: _cholesterol,
                      hint: 'e.g. 200',
                      description: 'Enter the value in mg/dL.',
                      decimal: true,
                      validator: (value) =>
                          _positiveNumber(value, field: 'cholesterol'),
                    ),
                    _numberField(
                      label: 'BMI',
                      controller: _bmi,
                      hint: 'Enter a positive number',
                      decimal: true,
                      validator: (value) =>
                          _positiveNumber(value, field: 'BMI'),
                    ),
                    _selectField(
                      label: 'Smoker',
                      value: _smoker,
                      items: _yesNoItems(),
                      onChanged: (value) => setState(() => _smoker = value),
                    ),
                    _selectField(
                      label: 'Diabetes',
                      value: _diabetes,
                      items: _yesNoItems(),
                      onChanged: (value) => setState(() => _diabetes = value),
                    ),
                    _selectField(
                      label: 'Physical activity',
                      value: _activity,
                      items: List.generate(
                        5,
                        (value) => DropdownMenuItem(
                          value: value,
                          child: Text('$value'),
                        ),
                      ),
                      onChanged: (value) => setState(() => _activity = value),
                    ),
                    _selectField(
                      label: 'Family history',
                      value: _familyHistory,
                      items: _yesNoItems(),
                      onChanged: (value) =>
                          setState(() => _familyHistory = value),
                    ),
                    _selectField(
                      label: 'Stress level',
                      value: _stress,
                      items: List.generate(
                        9,
                        (index) => DropdownMenuItem(
                          value: index + 1,
                          child: Text('${index + 1}'),
                        ),
                      ),
                      onChanged: (value) => setState(() => _stress = value),
                    ),
                  ], constraints.maxWidth);
                },
              ),
              const SizedBox(height: 4),
              SizedBox(
                height: 54,
                child: FilledButton.icon(
                  onPressed: _loading ? null : _check,
                  icon: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.favorite_outline_rounded),
                  label: Text(_loading ? 'CHECKING…' : 'CHECK'),
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF167D74),
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.1,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _loading ? null : _reset,
                icon: const Icon(Icons.restart_alt_rounded),
                label: const Text('RESET'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                  foregroundColor: const Color(0xFF365653),
                  side: const BorderSide(color: Color(0xFFD4E1DE)),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(15),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _resultCard() {
    final result = _result;
    final color = result == null
        ? const Color(0xFF167D74)
        : result.hasHeartDisease
        ? const Color(0xFFB54735)
        : const Color(0xFF167D74);
    final title = result == null
        ? 'Prediction unavailable'
        : result.hasHeartDisease
        ? 'Likely to Have Heart Disease'
        : 'Unlikely to Have Heart Disease';
    final probability = result?.probability;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFEAF4F2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFD6E9E5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'HEART DISEASE PREDICTION RESULT',
            style: TextStyle(
              fontSize: 11,
              letterSpacing: 1.0,
              fontWeight: FontWeight.w800,
              color: Color(0xFF526B67),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                result == null ? Icons.info_outline : Icons.favorite,
                color: color,
                size: 23,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              if (probability != null)
                Text(
                  '${(probability * 100).toStringAsFixed(1)}%',
                  style: TextStyle(
                    color: color,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            result != null
                ? 'This is an estimate from the connected model and is not a diagnosis.'
                : _message ??
                      'Complete the form and connect the trained model to receive an estimate.',
            style: const TextStyle(
              color: Color(0xFF526B67),
              height: 1.45,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _disclaimerCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E8),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF0E2BB)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.health_and_safety_outlined,
            color: Color(0xFF8B6A21),
            size: 20,
          ),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              _disclaimer,
              style: TextStyle(
                color: Color(0xFF66552E),
                height: 1.45,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
