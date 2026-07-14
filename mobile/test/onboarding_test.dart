import 'package:artapp/api.dart';
import 'package:artapp/screens/onboarding.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Hoş geldin ekranı üç seçeneği gösterir', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
    expect(find.text('Misafir Olarak Devam Et'), findsOneWidget);
    expect(find.text('Giriş Yap (yakında)'), findsOneWidget);
    expect(find.text('Kayıt Ol (yakında)'), findsOneWidget);
  });

  testWidgets('Sonuç ekranı seviye ve eksenleri listeler', (tester) async {
    final assessment = Assessment.fromJson({
      'level': 2,
      'ability_scores': {'anatomi': 40, 'perspektif': 55},
      'summary_tr': 'Güzel bir başlangıç!',
      'focus_axes': ['anatomi'],
    });
    await tester.pumpWidget(MaterialApp(home: ResultScreen(assessment: assessment)));
    expect(find.text('2. Seviye'), findsOneWidget);
    expect(find.text('Anatomi'), findsOneWidget);
    expect(find.text('40/100 — belirlendi'), findsOneWidget);
  });
}
