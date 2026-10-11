import 'dart:typed_data';

import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/assignment_card.dart';
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

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Scaffold(body: SingleChildScrollView(child: child)),
    );

void main() {
  testWidgets('Yapılandırılmış ödev: amaç, numaralı adımlar, kontrol listesi, süre',
      (tester) async {
    final brief = AssignmentBrief.fromJson({
      'goal_tr': 'Kupayı farklı açılardan çiz.',
      'steps_tr': ['Bir kupa fotoğrafı bul.', 'Üç açıdan çiz.'],
      'success_criteria_tr': ['Kupa 3 açıdan çizilmiş.'],
      'time_minutes': 30,
    });
    await tester.pumpWidget(_wrap(AssignmentCard(text: 'düz metin', brief: brief)));
    expect(find.text('Amaç'), findsOneWidget);
    expect(find.text('Kupayı farklı açılardan çiz.'), findsOneWidget);
    expect(find.text('2'), findsOneWidget); // numaralı adım
    expect(find.text('Kontrol listesi'), findsOneWidget);
    expect(find.text('~30 dk'), findsOneWidget);
    expect(find.text('düz metin'), findsNothing);
  });

  testWidgets('Eski ödev (brief yok): düz metin gösterilir', (tester) async {
    await tester.pumpWidget(_wrap(const AssignmentCard(text: 'Eski ödev metni')));
    expect(find.text('Eski ödev metni'), findsOneWidget);
    expect(find.text('Amaç'), findsNothing);
  });

  testWidgets('Sonuç: kontrol listesi, AI ne gördü notu ve sıradaki adım',
      (tester) async {
    final analysis = RedlineResult.fromJson({
      'strengths_tr': ['Çizgiler kararlı.'],
      'findings': [],
      'overall_comment_tr': 'Genel okuma.',
      'next_step_tr': 'Kupayı 3 açıdan çiz.',
      'task_match': 17,
      'task_passed': false,
      'subject_matches': false,
      'drawing_description_tr': 'Bir manzara çizimi.',
      'task_checks': [
        {'criterion_tr': 'Kupa var', 'status': 'missing'},
        {'criterion_tr': 'Yapı çizgileri', 'status': 'partial'},
        {'criterion_tr': 'Temiz çizgi', 'status': 'met'},
      ],
    });
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: RedlineScreen(image: MemoryImage(_png), analysis: analysis),
    ));
    await tester.pump();
    expect(find.text('Kupa var'), findsOneWidget);
    expect(find.byIcon(Icons.cancel_outlined), findsOneWidget);
    expect(find.byIcon(Icons.contrast), findsOneWidget);
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
    expect(find.text('AI çizimde şunu gördü: Bir manzara çizimi.'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Sıradaki adım'), 300);
    expect(find.text('Kupayı 3 açıdan çiz.'), findsOneWidget);
  });
}
