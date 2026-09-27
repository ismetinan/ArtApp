import 'dart:convert';

import 'package:artapp/api.dart';
import 'package:artapp/l10n/gen/app_localizations.dart';
import 'package:artapp/update_check.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

MockClient _cfg(Map<String, dynamic> body) => MockClient((_) async =>
    http.Response.bytes(utf8.encode(jsonEncode(body)), 200,
        headers: {'content-type': 'application/json'}));

Future<void> _run(WidgetTester tester, Map<String, dynamic> cfg) async {
  await http.runWithClient(() async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Builder(builder: (context) {
        return TextButton(
            onPressed: () => checkForUpdate(context), child: const Text('kontrol'));
      }),
    ));
    await tester.tap(find.text('kontrol'));
    await tester.pumpAndSettle();
  }, () => _cfg(cfg));
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    ApiClient.instance.appVersion = '1.1.0+25';
  });

  test('sürüm karşılaştırması sayısal, sözlük sırası değil', () {
    expect(compareVersions('1.10.0', '1.9.2'), 1);
    expect(compareVersions('0.10.0', '1.0'), -1);
    expect(compareVersions('1.1', '1.1.0'), 0);
    expect(compareVersions('1.1.0+25', '1.1.0'), 0);
    expect(compareVersions('1.0.9', '1.1.0'), -1);
  });

  testWidgets('güncel sürümde diyalog çıkmaz', (tester) async {
    await _run(tester, {'latest_version': '1.1.0', 'min_version': null, 'store_url': 'x'});
    expect(find.byType(AlertDialog), findsNothing);
  });

  testWidgets('öneri: "Sonra" ile kapanır, aynı sürüm için tekrar sorulmaz',
      (tester) async {
    final cfg = {'latest_version': '1.2.0', 'min_version': null, 'store_url': 'x'};
    await _run(tester, cfg);
    expect(find.text('Yeni sürüm hazır'), findsOneWidget);
    await tester.tap(find.text('Sonra'));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    await _run(tester, cfg);
    expect(find.byType(AlertDialog), findsNothing);
  });

  testWidgets('zorunlu: kapatılamaz, "Sonra" yok', (tester) async {
    await _run(tester, {'latest_version': '1.3.0', 'min_version': '1.2.0', 'store_url': 'x'});
    expect(find.text('Güncelleme gerekiyor'), findsOneWidget);
    expect(find.text('Sonra'), findsNothing);
    await tester.tapAt(const Offset(5, 5)); // bariyere dokun
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekiyor'), findsOneWidget);
  });
}
