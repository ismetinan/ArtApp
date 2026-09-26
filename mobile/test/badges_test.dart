import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/badges.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Scaffold(body: child),
    );

BadgeInfo _b(String code, String icon, String title) => BadgeInfo.fromJson(
    {'code': code, 'icon': icon, 'title': title, 'description': '$title açıklama'});

void main() {
  testWidgets('Kampanya kutlaması rozet + jeton metnini gösterir', (tester) async {
    await tester.pumpWidget(_wrap(Builder(
      builder: (context) => TextButton(
        onPressed: () => showCelebration(
            context, Celebration([_b('founding_artist', 'rocket', 'Kurucu Çizer')], 10)),
        child: const Text('aç'),
      ),
    )));
    await tester.tap(find.text('aç'));
    await tester.pumpAndSettle();
    expect(find.text('Kurucu Çizer'), findsOneWidget);
    expect(find.textContaining('10 jeton'), findsOneWidget);
    expect(find.byIcon(Icons.rocket_launch), findsOneWidget);
    await tester.tap(find.text('Harika!'));
    await tester.pumpAndSettle();
    expect(find.text('Kurucu Çizer'), findsNothing);
  });

  testWidgets('Rozet şeridi bilinmeyen ikonu kupaya düşürür', (tester) async {
    await tester.pumpWidget(_wrap(BadgeStrip(badges: [
      _b('first_lesson', 'school', 'İlk Adım'),
      _b('future_badge', 'bilinmeyen', 'Gelecek'),
    ])));
    expect(find.byIcon(Icons.school), findsOneWidget);
    expect(find.byIcon(Icons.emoji_events), findsOneWidget);
    await tester.tap(find.text('İlk Adım'));
    await tester.pump();
    expect(find.text('İlk Adım: İlk Adım açıklama'), findsOneWidget);
  });
}
