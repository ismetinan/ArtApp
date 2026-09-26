import 'dart:convert';
import 'dart:io';

import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/screens/admin_analytics.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Fikstür, backend'in GERÇEK /admin/analytics yanıtlarından üretildi
/// (test/fixtures/admin_analytics.json) — sözleşme bozulursa bu test kırılır.
Map<String, dynamic> _fixture() {
  final data = jsonDecode(File('test/fixtures/admin_analytics.json').readAsStringSync())
      as Map<String, dynamic>;
  // Olgunlaşmış bir kohort ekle ki retention hücreleri de çizilsin
  (data['retention']['cohorts'] as List).first
    ..['size'] = 3
    ..['w1'] = 0.667
    ..['w2'] = 0.333;
  return data;
}

MockClient _client(Map<String, dynamic> data) => MockClient((req) async {
      final section = req.url.pathSegments.last;
      final body = data[section];
      if (body == null) return http.Response('{"detail":"yok"}', 404);
      return http.Response.bytes(utf8.encode(jsonEncode(body)), 200,
          headers: {'content-type': 'application/json'});
    });

Widget _wrap(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Scaffold(body: child),
    );

void main() {
  testWidgets('Analitik sekmesi gerçek yanıtlarla telefon genişliğinde çizilir',
      (tester) async {
    tester.view.physicalSize = const Size(360 * 3, 780 * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    final data = _fixture();
    await http.runWithClient(() async {
      await tester.pumpWidget(_wrap(const AdminAnalyticsTab()));
      await tester.pumpAndSettle();
    }, () => _client(data));

    expect(find.text('Genel bakış'), findsOneWidget);
    expect(find.text('Toplam kullanıcı'), findsOneWidget);
    // Admin hariç 3 gerçek kullanıcı
    expect(find.text('${data['overview']['users_total']}'), findsWidgets);

    await tester.scrollUntilVisible(find.text('Huni'), 300);
    expect(find.text('Ders tamamladı'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Retention (haftalık kohort)'), 300);
    expect(find.text('%67'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Ekonomi'), 300);
    await tester.scrollUntilVisible(find.text('Kullanıcı listesi (anonim)'), 300);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Anonim kullanıcı listesi #id gösterir, isim göstermez', (tester) async {
    tester.view.physicalSize = const Size(360 * 3, 780 * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    final data = _fixture();
    await http.runWithClient(() async {
      await tester.pumpWidget(MaterialApp(
        locale: const Locale('tr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: const [Locale('en'), Locale('tr')],
        home: const AdminUsersScreen(),
      ));
      await tester.pumpAndSettle();
    }, () => _client(data));

    final firstId = (data['users']['users'] as List).first['id'];
    expect(find.text('Kullanıcı #$firstId'), findsOneWidget);
    expect(find.textContaining('u0'), findsNothing); // görünen ad sızmıyor
    expect(tester.takeException(), isNull);
  });
}
