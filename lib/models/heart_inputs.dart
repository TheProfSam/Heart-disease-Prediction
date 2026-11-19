/// User-entered values, kept separate from UI controllers.
///
/// This object intentionally does not define a model feature order. The order,
/// units, and preprocessing must come from the supplied model's training
/// metadata before inference can be safely enabled.
class HeartInputs {
  const HeartInputs({
    required this.age,
    required this.sex,
    required this.bloodPressure,
    required this.cholesterol,
    required this.bmi,
    required this.smoker,
    required this.diabetes,
    required this.physicalActivity,
    required this.familyHistory,
    required this.stressLevel,
  });

  final int age;
  final int sex;
  final double bloodPressure;
  final double cholesterol;
  final double bmi;
  final int smoker;
  final int diabetes;
  final int physicalActivity;
  final int familyHistory;
  final int stressLevel;
}
