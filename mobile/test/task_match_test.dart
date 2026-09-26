import 'dart:typed_data';

import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/redline.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

final _png = Uint8List.fromList([
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48,
  0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00,
  0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54, 0x78,
  0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
  0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
]);

Future<void> _pump(WidgetTester tester, Map<String, dynamic> extra, {int xp = 0}) async {
  final analysis = RedlineResult.fromJson({
    'strengths_tr': ['Güçlü'],
    'findings': [],
    'overall_comment_tr': 'Genel',
    ...extra,
  });
  await tester.pumpWidget(MaterialApp(
    locale: const Locale('tr'),
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: const [Locale('en'), Locale('tr')],
    home: RedlineScreen(image: MemoryImage(_png), analysis: analysis, xpAwarded: xp),
  ));
  await tester.pump();
}

void main() {
  testWidgets('Uyumsuz ödev: uyum yüzdesi + tamamlanmadı notu', (tester) async {
    await _pump(tester, {
      'task_match': 15,
      'task_match_comment_tr': 'Görevdeki kupa yok.',
      'task_passed': false,
    });
    expect(find.text('Ödev uyumu: %15'), findsOneWidget);
    expect(find.text('Görevdeki kupa yok.'), findsOneWidget);
    expect(find.textContaining('ders tamamlanmadı'), findsOneWidget);
  });

  testWidgets('Uyumlu ödev: not yok, XP kartı var', (tester) async {
    await _pump(tester, {'task_match': 80, 'task_passed': true}, xp: 50);
    expect(find.text('Ödev uyumu: %80'), findsOneWidget);
    expect(find.textContaining('ders tamamlanmadı'), findsNothing);
  });

  testWidgets('Eski kayıt (task_match yok): kart gösterilmez', (tester) async {
    await _pump(tester, {});
    expect(find.textContaining('Ödev uyumu'), findsNothing);
  });
}
