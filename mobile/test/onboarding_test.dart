import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/onboarding.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child, {Locale locale = const Locale('tr')}) => MaterialApp(
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: child,
    );

void main() {
  testWidgets('Hoş geldin ekranı üç seçeneği gösterir', (tester) async {
    await tester.pumpWidget(_wrap(const WelcomeScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Misafir Olarak Devam Et'), findsOneWidget);
    expect(find.text('Giriş Yap'), findsOneWidget);
    expect(find.text('Kayıt Ol'), findsOneWidget);
  });

  testWidgets('Welcome screen renders in English', (tester) async {
    await tester.pumpWidget(
        _wrap(const WelcomeScreen(), locale: const Locale('en')));
    await tester.pumpAndSettle();
    expect(find.text('Continue as Guest'), findsOneWidget);
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Sign Up'), findsOneWidget);
  });

  testWidgets('Sonuç ekranı seviye ve eksenleri listeler', (tester) async {
    final assessment = Assessment.fromJson({
      'level': 2,
      'ability_scores': {'anatomi': 40, 'perspektif': 55},
      'summary_tr': 'Güzel bir başlangıç!',
      'focus_axes': ['anatomi'],
    });
    await tester.pumpWidget(_wrap(ResultScreen(assessment: assessment)));
    await tester.pumpAndSettle();
    expect(find.text('2. Seviye'), findsOneWidget);
    expect(find.text('Anatomi'), findsOneWidget);
    expect(find.text('40/100 — belirlendi'), findsOneWidget);
  });
}
